import re
import logging
from typing import Dict, Any, Optional, List
from django.utils import timezone
from students.models import StudentProfile
from ai_assistant.models import (
    AIConversation,
    AIMessage,
    AIUsageLog,
    ConversationState
)
from .gemini_client import gemini_client
from .vex_context import VEXContextService
from .vex_memory import VEXMemoryService
from .vex_tools import VEXToolService
from .vex_safety import VEXSafetyService
from .vex_context_resolver import VEXContextResolver

try:
    from google.genai import types
    GENAI_TYPES_AVAILABLE = True
except ImportError:
    GENAI_TYPES_AVAILABLE = False

logger = logging.getLogger(__name__)


class VEXConversationService:
    """
    Core conversational orchestration engine for Novus.
    Maintains persistent conversation identity, structured state across turns,
    context-aware follow-up resolution, and multi-turn Gemini SDK messaging.
    """

    @classmethod
    def get_or_create_conversation(
        cls,
        student: StudentProfile,
        conversation_id: Optional[int] = None
    ) -> AIConversation:
        """
        Retrieves active conversation for the student, or initializes a new one.
        Strict student data isolation is enforced.
        """
        if conversation_id:
            try:
                return AIConversation.objects.get(id=conversation_id, student=student, is_archived=False)
            except AIConversation.DoesNotExist:
                pass

        # Return latest active conversation if one exists
        latest = AIConversation.objects.filter(student=student, is_archived=False).order_by('-updated_at').first()
        if latest:
            return latest

        # Create new conversation only when no active conversation exists
        conv = AIConversation.objects.create(
            student=student,
            title='Career & Learning Consultation'
        )
        ConversationState.objects.get_or_create(conversation=conv)
        return conv

    @classmethod
    def process_message(
        cls,
        student: StudentProfile,
        message_text: str,
        conversation_id: Optional[int] = None,
        context_action: Optional[str] = None,
        action_params: Optional[dict] = None
    ) -> Dict[str, Any]:
        """
        Main message processing pipeline with structured state tracking.
        """
        conversation = cls.get_or_create_conversation(student, conversation_id)
        state = conversation.current_state

        # 1. Safety validation
        is_safe, error_msg = VEXSafetyService.check_input_safety(message_text)
        if not is_safe:
            safety_msg = AIMessage.objects.create(
                conversation=conversation,
                role=AIMessage.Role.ASSISTANT,
                content=error_msg
            )
            return {
                'conversation_id': conversation.id,
                'message_id': safety_msg.id,
                'role': 'assistant',
                'content': safety_msg.content,
                'structured_data': None,
                'state': state.to_dict(),
                'created_at': safety_msg.created_at.strftime('%H:%M'),
            }

        # 2. Check for duplicate rapid retries to prevent duplicate messages
        from django.utils import timezone
        last_user_msg = conversation.messages.filter(role=AIMessage.Role.USER).order_by('-id').first()
        if last_user_msg and last_user_msg.content.strip() == message_text.strip():
            elapsed = (timezone.now() - last_user_msg.created_at).total_seconds()
            if elapsed < 2.0:
                next_msg = conversation.messages.filter(id__gt=last_user_msg.id, role=AIMessage.Role.ASSISTANT).first()
                if not next_msg:
                    next_msg = conversation.messages.filter(role=AIMessage.Role.ASSISTANT).order_by('-id').first()
                if next_msg:
                    return {
                        'conversation_id': conversation.id,
                        'message_id': next_msg.id,
                        'role': 'assistant',
                        'content': next_msg.content,
                        'structured_data': next_msg.structured_data,
                        'state': state.to_dict(),
                        'created_at': next_msg.created_at.strftime('%H:%M'),
                    }

        # 3. Record User Message
        user_msg = AIMessage.objects.create(
            conversation=conversation,
            role=AIMessage.Role.USER,
            content=message_text
        )

        # 4. Contextual Follow-up & Intent Resolution
        structured_data, tool_log, resolved_text = VEXContextResolver.resolve_turn(
            student=student,
            message_text=message_text,
            conversation=conversation,
            action=context_action,
            params=action_params
        )

        # 5. Gemini Generation or Deterministic Fallback
        tokens_used = 0
        final_text = ""

        # If Gemini is configured and we don't have a strict deterministic response
        if gemini_client.is_configured:
            strict_actions = ['application_confirmation', 'application_success']
            if structured_data and structured_data.get('type') in strict_actions:
                final_text = resolved_text
            else:
                gemini_payload = cls._build_gemini_multiturn_payload(conversation, user_msg, structured_data)
                system_instruction = VEXContextService.build_system_instruction(student)

                gemini_result = gemini_client.generate_content(
                    contents=gemini_payload,
                    system_instruction=system_instruction,
                    temperature=0.7
                )

                if gemini_result['success'] and gemini_result['text']:
                    final_text = VEXSafetyService.sanitize_output(gemini_result['text'])
                    tokens_used = gemini_result['tokens_used']
                    AIUsageLog.objects.create(
                        student=student,
                        prompt_tokens=int(tokens_used * 0.6),
                        candidate_tokens=int(tokens_used * 0.4),
                        model_name=gemini_client.model_name,
                        action_type=context_action or state.active_intent or 'chat'
                    )
                else:
                    final_text = resolved_text or cls._generate_deterministic_fallback(
                        student=student,
                        message_text=message_text,
                        structured_data=structured_data,
                        conversation=conversation,
                        state=state
                    )
        else:
            final_text = resolved_text or cls._generate_deterministic_fallback(
                student=student,
                message_text=message_text,
                structured_data=structured_data,
                conversation=conversation,
                state=state
            )

        # Apply Anti-Repetition Guard
        final_text = cls._ensure_non_repetitive(conversation, final_text, student)

        # 6. Save Assistant Message
        assistant_msg = AIMessage.objects.create(
            conversation=conversation,
            role=AIMessage.Role.ASSISTANT,
            content=final_text,
            structured_data=structured_data,
            tool_calls=tool_log,
            tokens_used=tokens_used
        )

        # 7. Extract Long-Term Memories
        try:
            VEXMemoryService.extract_memories_from_text(
                student=student,
                user_message=message_text,
                assistant_message=final_text,
                conversation=conversation
            )
        except Exception as e:
            logger.error(f"Memory extraction error: {e}")

        # 8. Update conversation title if needed
        if conversation.messages.count() <= 3:
            words = message_text.split()[:5]
            if words:
                conversation.title = " ".join(words).capitalize()[:60]
                conversation.save(update_fields=['title', 'updated_at'])
        else:
            conversation.save(update_fields=['updated_at'])

        return {
            'conversation_id': conversation.id,
            'message_id': assistant_msg.id,
            'role': 'assistant',
            'content': assistant_msg.content,
            'structured_data': assistant_msg.structured_data,
            'state': state.to_dict(),
            'tokens_used': assistant_msg.tokens_used,
            'created_at': assistant_msg.created_at.strftime('%H:%M'),
        }

    @classmethod
    def _build_gemini_multiturn_payload(
        cls,
        conversation: AIConversation,
        current_user_msg: AIMessage,
        structured_data: Optional[dict] = None
    ) -> Any:
        """
        Builds multi-turn contents list for the official Google Gen AI SDK.
        Preserves role turns and includes tool context.
        """
        history_msgs = conversation.messages.exclude(id=current_user_msg.id).order_by('created_at')[:10]

        if GENAI_TYPES_AVAILABLE:
            contents = []
            for m in history_msgs:
                role = "user" if m.role == AIMessage.Role.USER else "model"
                content_text = m.content
                if m.role == AIMessage.Role.ASSISTANT and m.structured_data:
                    # Provide concise tool summary to model context
                    s_type = m.structured_data.get('type')
                    content_text += f"\n[Context Data Shown to User: {s_type}]"

                contents.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=content_text)])
                )

            # Add current user prompt
            user_text = current_user_msg.content
            if structured_data:
                user_text += f"\n\n[Active Tool Output Retrieved from NexGrad DB]: {structured_data}"

            contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=user_text)])
            )
            return contents

        # Fallback to plain string if SDK types are not loaded
        lines = []
        for m in history_msgs:
            role = "USER" if m.role == AIMessage.Role.USER else "ASSISTANT"
            lines.append(f"{role}: {m.content}")
        lines.append(f"USER: {current_user_msg.content}")
        return "\n\n".join(lines)

    @classmethod
    def _generate_deterministic_fallback(
        cls,
        student: StudentProfile,
        message_text: str,
        structured_data: Optional[dict] = None,
        conversation: Optional[AIConversation] = None,
        state: Optional[ConversationState] = None
    ) -> str:
        """
        Deterministic, context-aware fallback response generator.
        Grounded in active conversation state and student records.
        NEVER outputs the welcome message on a follow-up turn.
        """
        student_name = student.user.get_full_name() or student.user.username
        branch = student.get_branch_display()
        cgpa = student.cgpa

        # If structured data was retrieved, provide specific explanation
        if structured_data:
            s_type = structured_data.get('type')
            data = structured_data.get('data', {})

            if s_type == 'job_list':
                count = data.get('count', 0)
                return (
                    f"I identified **{count} high-compatibility engineering opportunities** matching your {branch} background (CGPA: {cgpa}):\n\n"
                    f"You can explore the opportunity cards below, ask **'Show the first one'** for complete specifications, or **'Apply for job 1'**."
                )

            elif s_type == 'job_detail':
                return (
                    f"Here are the complete specifications for **{data.get('title')}** at **{data.get('company')}**:\n\n"
                    f"- **Location:** {data.get('location')} ({data.get('workplace_type')})\n"
                    f"- **Compensation:** {data.get('salary_range')}\n"
                    f"- **Your Match:** **{data.get('match_percentage')}% Match** ({'Eligible' if data.get('is_fully_eligible') else 'Check Specs'})\n\n"
                    f"Would you like me to submit an application draft for this position?"
                )

            elif s_type == 'internship_list':
                count = data.get('count', 0)
                return (
                    f"Here are **{count} targeted internship programs** currently active on NexGrad, {student_name}.\n\n"
                    f"Each listing shows your current skill affinity match and stipend. Check the program cards below."
                )

            elif s_type == 'skill_matrix':
                role = data.get('target_role', 'Engineering')
                readiness = data.get('readiness_score', 0)
                return (
                    f"Here is your targeted **Skill Gap Analysis for {role}**, {student_name}.\n\n"
                    f"Based on your profile, you match **{readiness}%** of industry requirements on NexGrad. "
                    f"Ask me **'How do I improve it?'** to get targeted project ideas."
                )

            elif s_type == 'learning_roadmap':
                role = data.get('target_role', 'Engineering')
                weeks = data.get('duration_weeks', 12)
                return (
                    f"I have constructed a comprehensive **{weeks}-Week Mastery Roadmap for {role}**, customized specifically for you, {student_name}.\n\n"
                    f"Say **'Start week one'** to inspect your first set of engineering tasks."
                )

            elif s_type == 'mock_interview':
                if data.get('is_finished'):
                    return (
                        f"🎉 **Mock Interview Completed**, {student_name}!\n\n"
                        f"**Overall Rating:** {data.get('overall_score', 0)}/10.\n\n"
                        f"{data.get('summary')}"
                    )
                else:
                    q_num = data.get('question_number', 1)
                    q_text = data.get('question_text', '')
                    feedback_lead = ""
                    if data.get('last_feedback'):
                        last_f = data['last_feedback']
                        feedback_lead = f"**Previous Answer Evaluation:** Score {last_f['score']}/10.\n*{last_f['feedback']}*\n\n---\n\n"
                    return (
                        f"{feedback_lead}**Mock Interview — Question {q_num} of {data.get('total_questions', 3)}**:\n\n"
                        f"> {q_text}\n\n"
                        f"Type your answer directly in the box below to receive instant rubric scoring."
                    )

            elif s_type == 'resume_analysis':
                role = data.get('target_role', 'Engineering')
                return (
                    f"Here is your **Resume & Profile Audit for {role}**, {student_name}.\n\n"
                    f"I reviewed your registered projects, academic credentials, and skill tags. "
                    f"Ask me **'Fix these issues'** to see rewritten Google XYZ bullet points."
                )

            elif s_type == 'applications_summary':
                total = data.get('total_applications', 0)
                return (
                    f"You currently have **{total} application(s)** in your NexGrad pipeline, {student_name}.\n\n"
                    f"Review the status cards below or ask me about any specific application."
                )

            elif s_type == 'assessment_summary':
                total = data.get('total_assessments', 0)
                return (
                    f"Here is your **Technical Assessment Record**, {student_name}.\n\n"
                    f"You have completed {total} formal assessments on NexGrad."
                )

        # Context-dependent fallback (NEVER repeat initial welcome greeting on follow-ups!)
        if conversation and conversation.messages.count() > 1:
            if state and state.active_task == 'job_search_results' and state.active_entity_ids:
                return (
                    f"We currently have **{len(state.active_entity_ids)} matching opportunities** active in this consultation.\n\n"
                    f"You can ask me:\n"
                    f"- *'Show me'* to view the opportunity cards\n"
                    f"- *'Show the first one'* for full role breakdown\n"
                    f"- *'Compare the first and second jobs'*\n"
                    f"- *'Apply for job 1'*"
                )
            elif state and state.active_task == 'viewing_job_detail':
                return (
                    f"You are currently viewing details for **{state.metadata.get('selected_job_title', 'the selected position')}**.\n\n"
                    f"Would you like to **'Apply for this job'**, **'Compare with another'**, or explore **'More jobs'**?"
                )
            elif state and state.active_task == 'awaiting_application_confirmation':
                return "Please reply **'Confirm'** to officially submit your application or **'Cancel'** to withdraw."

            # Dynamic intelligent fallback via Intent Router
            from .vex_intent_router import VEXIntentRouter
            intent, extracted_params = VEXIntentRouter.classify_intent(
                message_text=message_text,
                student=student,
                state=state
            )
            _, _, text = VEXIntentRouter.execute_and_respond(
                intent=intent,
                student=student,
                conversation=conversation,
                state=state,
                params=extracted_params,
                message_text=message_text
            )
            return text

        # If user typed an initial message on a brand new conversation
        if message_text and message_text.strip():
            from .vex_intent_router import VEXIntentRouter
            intent, extracted_params = VEXIntentRouter.classify_intent(
                message_text=message_text,
                student=student,
                state=state
            )
            _, _, text = VEXIntentRouter.execute_and_respond(
                intent=intent,
                student=student,
                conversation=conversation,
                state=state,
                params=extracted_params,
                message_text=message_text
            )
            return text

        # Only on an empty brand-new conversation with zero prior interaction
        return (
            f"Hello {student_name}! I'm Novus, your personal career companion at NexGrad.\n\n"
            f"As a {branch} student (CGPA: {cgpa}), you have several tailored pathways available on NexGrad:\n"
            f"- **Find Matching Jobs & Internships**: Ask me to find opportunities tailored to your skills.\n"
            f"- **Skill Gap Analysis**: Tell me your target role to see missing competencies.\n"
            f"- **Generate a Learning Roadmap**: Ask for a study plan to master new technologies.\n"
            f"- **Mock Interview**: Practice real-world technical questions with instant feedback.\n\n"
            f"What would you like to work on today?"
        )

    @classmethod
    def _ensure_non_repetitive(
        cls,
        conversation: AIConversation,
        candidate_text: str,
        student: StudentProfile
    ) -> str:
        """
        Guarantees that the assistant never emits a response substantially identical
        to recent assistant turns, and eliminates boilerplate repetitive loops.
        """
        if not candidate_text:
            return candidate_text

        text = candidate_text.strip()
        first_name = student.user.first_name or student.user.username
        branch = student.get_branch_display()

        # Check last assistant message in this conversation
        prev_assistant_msg = conversation.messages.filter(role=AIMessage.Role.ASSISTANT).order_by('-id').first()
        if prev_assistant_msg:
            prev_text = prev_assistant_msg.content.strip()

            # 1. Exact match check
            if text.lower() == prev_text.lower():
                return f"I'm right here with you, {first_name}. Feel free to ask about active jobs, explore career paths for {branch}, or practice technical interview questions."

            # 2. High word overlap (> 85%) on conversational responses
            words_cand = set(re.findall(r'\w+', text.lower()))
            words_past = set(re.findall(r'\w+', prev_text.lower()))
            if words_cand and words_past and len(words_cand) > 5:
                overlap = len(words_cand.intersection(words_past)) / max(len(words_cand), len(words_past))
                if overlap > 0.85:
                    return f"As we discussed, {first_name}, whenever you're ready we can explore active vacancies, analyze your skill gaps, or prepare for placements. What would you like to do?"

        return text
