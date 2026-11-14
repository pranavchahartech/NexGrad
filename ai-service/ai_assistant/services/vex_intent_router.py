import re
import logging
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List
from django.utils import timezone
from students.models import StudentProfile
from jobs.models import Job
from ai_assistant.models import AIConversation, ConversationState, AIMessage
from .vex_tools import VEXToolService
from .gemini_client import gemini_client

logger = logging.getLogger(__name__)


class NovusIntent(str, Enum):
    # General conversation
    GREETING = 'greeting'
    FAREWELL = 'farewell'
    ACKNOWLEDGEMENT = 'acknowledgement'
    GRATITUDE = 'gratitude'
    CASUAL_CONVERSATION = 'casual_conversation'
    CLARIFICATION = 'clarification'
    HELP_REQUEST = 'help_request'

    # Career intelligence
    JOB_SEARCH = 'job_search'
    INTERNSHIP_SEARCH = 'internship_search'
    JOB_ELIGIBILITY = 'job_eligibility'
    JOB_DETAILS = 'job_details'
    JOB_COMPARISON = 'job_comparison'
    APPLICATION_STATUS = 'application_status'
    CAREER_GUIDANCE = 'career_guidance'
    CAREER_RECOMMENDATION = 'career_recommendation'

    # Learning
    SKILL_GAP_ANALYSIS = 'skill_gap_analysis'
    LEARNING_ROADMAP = 'learning_roadmap'
    LEARNING_RECOMMENDATION = 'learning_recommendation'
    TECHNICAL_EXPLANATION = 'technical_explanation'
    PROGRAMMING_HELP = 'programming_help'
    PROJECT_GUIDANCE = 'project_guidance'

    # Student support
    RESUME_ANALYSIS = 'resume_analysis'
    RESUME_IMPROVEMENT = 'resume_improvement'
    INTERVIEW_PREPARATION = 'interview_preparation'
    MOCK_INTERVIEW = 'mock_interview'
    ASSESSMENT_ANALYSIS = 'assessment_analysis'
    CHALLENGE_GUIDANCE = 'challenge_guidance'

    # Conversation management
    CONTINUE_PREVIOUS_TASK = 'continue_previous_task'
    SHOW_PREVIOUS_RESULTS = 'show_previous_results'
    SHOW_SELECTED_ENTITY = 'show_selected_entity'
    RETRIEVE_MORE_RESULTS = 'retrieve_more_results'
    NEW_CONVERSATION = 'new_conversation'
    APPLY_JOB = 'apply_job'
    CONFIRM_ACTION = 'confirm_action'
    CANCEL_ACTION = 'cancel_action'

    UNKNOWN = 'unknown'


class VEXIntentRouter:
    """
    Intelligent conversational intent classifier and execution router for Novus.
    Supports natural language classification, contextual state awareness,
    backend tool execution, and rich intent-specific response generation.
    """

    ORDINAL_MAP = {
        'first': 0, '1st': 0, '1': 0, 'one': 0,
        'second': 1, '2nd': 1, '2': 1, 'two': 1,
        'third': 2, '3rd': 2, '3': 2, 'three': 2,
        'fourth': 3, '4th': 3, '4': 3, 'four': 3,
    }

    # -------------------------------------------------------------------------
    # 1. INTENT CLASSIFICATION
    # -------------------------------------------------------------------------

    @classmethod
    def classify_intent(
        cls,
        message_text: str,
        student: StudentProfile,
        state: Optional[ConversationState] = None,
        action: Optional[str] = None,
        params: Optional[dict] = None
    ) -> Tuple[NovusIntent, Dict[str, Any]]:
        """
        Classifies incoming message into a NovusIntent with extracted parameters.
        Combines explicit UI action triggers, active conversational state,
        and natural language pattern semantics.
        """
        text = (message_text or '').strip()
        text_lower = text.lower()
        clean_text = re.sub(r'[\.\?\!\,\;]+$', '', text_lower).strip()
        extracted_params: Dict[str, Any] = dict(params or {})

        # A. Explicit UI actions from frontend chips/buttons
        if action:
            action_map = {
                'find_jobs': NovusIntent.JOB_SEARCH,
                'find_internships': NovusIntent.INTERNSHIP_SEARCH,
                'skill_gap': NovusIntent.SKILL_GAP_ANALYSIS,
                'create_roadmap': NovusIntent.LEARNING_ROADMAP,
                'mock_interview': NovusIntent.MOCK_INTERVIEW,
                'analyse_resume': NovusIntent.RESUME_ANALYSIS,
                'confirm_application': NovusIntent.CONFIRM_ACTION,
                'application_status': NovusIntent.APPLICATION_STATUS,
            }
            if action in action_map:
                return action_map[action], extracted_params

        # B. Active State Overrides (Context-aware responses)
        if state and state.active_task == 'awaiting_application_confirmation':
            if re.search(r'\b(yes|confirm|submit|apply|go ahead|proceed|sure|yep|do it|ok)\b', text_lower):
                return NovusIntent.CONFIRM_ACTION, extracted_params
            elif re.search(r'\b(no|cancel|stop|don\'t|wait|abort|nevermind)\b', text_lower):
                return NovusIntent.CANCEL_ACTION, extracted_params

        # C. Application Drafting Intent
        apply_match = re.search(
            r'\bapply\s+(?:for|to)?\s+(?:the\s+)?(first|1st|1|second|2nd|2|third|3rd|3|fourth|4th|4|this|it)\b',
            text_lower
        )
        if apply_match:
            ref = apply_match.group(1).lower()
            extracted_params['ordinal_ref'] = ref
            if ref in cls.ORDINAL_MAP:
                extracted_params['ordinal_idx'] = cls.ORDINAL_MAP[ref]
            return NovusIntent.APPLY_JOB, extracted_params

        # D. Job Comparison Intent
        compare_match = re.search(
            r'\bcompare\s+(?:the\s+)?(first|1st|1|second|2nd|2|third|3rd|3|fourth|4th|4)\s+(?:and|with|to)\s+(?:the\s+)?(first|1st|1|second|2nd|2|third|3rd|3|fourth|4th|4)\b',
            text_lower
        )
        if compare_match or re.search(r'\b(compare\s+(?:the\s+)?jobs|which\s+job\s+is\s+better|comparison)\b', text_lower):
            if compare_match:
                w1, w2 = compare_match.group(1).lower(), compare_match.group(2).lower()
                extracted_params['compare_idx1'] = cls.ORDINAL_MAP.get(w1, 0)
                extracted_params['compare_idx2'] = cls.ORDINAL_MAP.get(w2, 1)
            return NovusIntent.JOB_COMPARISON, extracted_params

        # E. Specific Entity Details by Ordinal or "Explain this job" / "Tell me more"
        ordinal_detail_match = re.search(
            r'\b(?:show|tell me about|details on|view|open|what about|describe|explain)\s+(?:the\s+)?(first|1st|1|second|2nd|2|third|3rd|3|fourth|4th|4|one|two|three|four)\b',
            clean_text
        ) or (not re.search(r'\bapply\b', clean_text) and re.search(
            r'\b(first|1st|second|2nd|third|3rd|fourth|4th)\s+(?:one|job|role|position|vacancy)\b',
            clean_text
        )) or re.search(
            r'\b(explain\s+(?:this\s+)?(?:job|role|position)|tell\s+me\s+more(?:\s+about\s+(?:this\s+)?(?:job|role|position))?|job\s+details|details\s+(?:on|about)\s+(?:this\s+)?(?:job|role))\b',
            clean_text
        ) or (state and state.active_entity_type == 'job' and clean_text in ['tell me more', 'details', 'explain'])
        if ordinal_detail_match:
            word = None
            if hasattr(ordinal_detail_match, 'group') and ordinal_detail_match.lastindex:
                word = ordinal_detail_match.group(1).lower()
            if word in cls.ORDINAL_MAP:
                extracted_params['ordinal_idx'] = cls.ORDINAL_MAP[word]
            else:
                extracted_params['ordinal_idx'] = 0
            return NovusIntent.JOB_DETAILS, extracted_params

        # F. Show Previous Results ("Show me", "Display results")
        if re.search(r'^(show me|show them|show results|display them|let me see|can you show|view jobs|view results|see them|show all)(\s+(jobs|results|openings|opportunities))?$', clean_text) or clean_text in ['show', 'show me', 'show them', 'show all', 'display all']:
            return NovusIntent.SHOW_PREVIOUS_RESULTS, extracted_params

        # G. More Results ("Are there any more?", "Show more jobs")
        if re.search(r'\b(more jobs|additional jobs|show more|any more|next jobs|other jobs)\b', text_lower):
            return NovusIntent.RETRIEVE_MORE_RESULTS, extracted_params

        # H. Job Search Intent (Natural phrases: "Is there any job?", "Find jobs for me", etc.)
        if re.search(
            r'\b(is\s+there\s+any\s+jobs?|are\s+there\s+(?:any\s+)?jobs?|any\s+jobs?|find\s+jobs?|search\s+jobs?|job\s+search|job\s+openings?|job\s+vacancies|suitable\s+vacancies|opportunities\s+for\s+me|jobs\s+for\s+me|what\s+jobs|available\s+jobs|show\s+(?:me\s+)?jobs|jobs\s+matching|recommend\s+jobs|suggest\s+(?:me\s+)?(?:a\s+)?(?:suitable\s+|best\s+)?job|eligible\s+jobs|matching\s+jobs)\b',
            text_lower
        ) or text_lower in ['jobs', 'job', 'find job', 'find jobs', 'search job']:
            # Extract keyword if present
            m_kw = re.search(r'(?:for|in|as)\s+([a-zA-Z\s]{3,20})(?:\s+roles?|\s+jobs?)?', text_lower)
            if m_kw and m_kw.group(1).strip() not in ['me', 'my profile', 'my branch', 'freshers']:
                extracted_params['keyword'] = m_kw.group(1).strip()
            return NovusIntent.JOB_SEARCH, extracted_params

        # I. Internship Search Intent ("Any internships available?", "Find internships")
        if re.search(r'\b(internships?|summer\s+internship|paid\s+internship|any\s+internship|find\s+internships?)\b', text_lower):
            return NovusIntent.INTERNSHIP_SEARCH, extracted_params

        # J. Job Eligibility Check ("Am I eligible?", "Check my eligibility")
        if re.search(r'\b(am\s+i\s+eligible|check\s+my\s+eligibility|do\s+i\s+qualify|is\s+it\s+eligible|my\s+eligibility|can\s+i\s+apply)\b', text_lower):
            return NovusIntent.JOB_ELIGIBILITY, extracted_params

        # K. Application Status ("Where did I apply?", "Check my applications")
        if re.search(r'\b(where\s+did\s+i\s+apply|check\s+my\s+applications?|application\s+status|track\s+(?:my\s+)?applications?|my\s+applications?|applied\s+status)\b', text_lower):
            return NovusIntent.APPLICATION_STATUS, extracted_params

        # L. Career Guidance ("What should I do?", "Which career is suitable for me?", "Where to start?")
        if re.search(
            r'\b(what\s+should\s+i\s+do|which\s+career\s+is\s+suitable|where\s+should\s+i\s+start|where\s+to\s+start|am\s+i\s+ready\s+for\s+placements|how\s+can\s+i\s+improve\s+my\s+profile|career\s+guidance|career\s+advice|what\s+career|career\s+options|what\s+path|how\s+to\s+prepare\s+for\s+placements)\b',
            text_lower
        ) or text_lower in ['what should i do', 'guide me', 'career help', 'what next']:
            return NovusIntent.CAREER_GUIDANCE, extracted_params

        # M. Career Recommendation ("What career suits my profile?", "Recommend a career path")
        if re.search(r'\b(what\s+career\s+suits?\s+(?:my\s+)?profile|recommend\s+(?:a\s+)?career|best\s+roles?\s+for\s+me)\b', text_lower):
            return NovusIntent.CAREER_RECOMMENDATION, extracted_params

        # N. Skill Gap Analysis ("Analyze my skill gaps", "What skills am I missing?")
        if re.search(r'\b(skill\s+gaps?|analyze\s+(?:my\s+)?skill\s+gaps?|missing\s+skills?|what\s+skills\s+am\s+i\s+missing|gap\s+analysis)\b', text_lower):
            m_role = re.search(r'(?:for|as a|become a)\s+([a-zA-Z\s]{3,25})', text_lower)
            if m_role:
                extracted_params['target_role'] = m_role.group(1).strip()
            return NovusIntent.SKILL_GAP_ANALYSIS, extracted_params

        # O. Learning Roadmap ("Generate a learning roadmap", "Create study plan")
        if re.search(r'\b(roadmaps?|learning\s+roadmaps?|study\s+plans?|learning\s+plans?|12-weeks?|curriculum)\b', text_lower):
            m_role = re.search(r'(?:for|to become|as a)\s+([a-zA-Z\s]{3,25})', text_lower)
            if m_role:
                extracted_params['target_role'] = m_role.group(1).strip()
            return NovusIntent.LEARNING_ROADMAP, extracted_params

        # P. Learning Recommendation ("What should I learn next?", "How do I improve it?", "What technologies to learn")
        if re.search(
            r'\b(what\s+should\s+i\s+learn(?:\s+next)?|how\s+do\s+i\s+improve\s+it|how\s+to\s+improve|what\s+technologies\s+should\s+i\s+learn|how\s+can\s+i\s+learn|what\s+to\s+study|how\s+do\s+i\s+improve)\b',
            text_lower
        ):
            return NovusIntent.LEARNING_RECOMMENDATION, extracted_params

        # Q. Resume Analysis & Audit ("Review my resume", "ATS score")
        if re.search(r'\b(review\s+(?:my\s+)?resume|resume\s+analysis|audit\s+(?:my\s+)?resume|ats\s+score|check\s+(?:my\s+)?resume|evaluate\s+(?:my\s+)?cv)\b', text_lower):
            return NovusIntent.RESUME_ANALYSIS, extracted_params

        # R. Resume Improvement ("Fix these issues", "Improve my resume", "Rewrite bullets")
        if re.search(r'\b(fix\s+(?:these\s+)?issues|improve\s+(?:my\s+)?resume|rewrite\s+bullets|xyz\s+formula|action\s+verbs|how\s+to\s+fix|bullet\s+points?)\b', text_lower):
            return NovusIntent.RESUME_IMPROVEMENT, extracted_params

        # S. Technical Mock Interview ("Start mock interview", "Practice interview", "Next question")
        if re.search(r'\b(mock\s+interviews?|practice\s+interviews?|start\s+(?:mock\s+)?interviews?|next\s+question|technical\s+interviews?)\b', text_lower):
            return NovusIntent.MOCK_INTERVIEW, extracted_params

        # T. Interview Preparation Guidance ("How to prepare for interviews?", "Interview tips")
        if re.search(r'\b(interview\s+prep|prepare\s+for\s+(?:tech\s+)?interviews?|interview\s+tips|common\s+interview\s+questions)\b', text_lower):
            return NovusIntent.INTERVIEW_PREPARATION, extracted_params

        # U. Assessment Analysis ("Explain my mistakes", "Why did I fail?", "Review assessment")
        if re.search(r'\b(explain\s+my\s+mistakes|review\s+assessments?|why\s+did\s+i\s+fail|assessments?\s+results?|my\s+score|test\s+results?)\b', text_lower):
            return NovusIntent.ASSESSMENT_ANALYSIS, extracted_params

        # V. Challenge Guidance ("Coding challenges", "Hackathon", "Solve challenges")
        if re.search(r'\b(coding\s+challenges?|hackathons?|contests?|solve\s+challenges?|dsa\s+practice)\b', text_lower):
            return NovusIntent.CHALLENGE_GUIDANCE, extracted_params

        # W. Project Guidance ("What projects should I build?", "Portfolio project ideas")
        if re.search(r'\b(what\s+projects\s+should\s+i\s+build|project\s+ideas|capstone\s+projects?|portfolio\s+projects?|suggest\s+projects?)\b', text_lower):
            return NovusIntent.PROJECT_GUIDANCE, extracted_params

        # X. Technical Explanation ("Explain Redis", "What is database indexing?", "How does Kafka work?")
        tech_exp_match = re.search(r'\b(?:explain|what\s+is|how\s+does)\s+([a-zA-Z0-9\s\+\#\-\.]+)(?:\s+work)?\b', text_lower)
        if tech_exp_match and not any(k in text_lower for k in ['job', 'resume', 'roadmap', 'interview', 'career', 'do']):
            concept = tech_exp_match.group(1).strip()
            if len(concept) > 2:
                extracted_params['concept'] = concept
                return NovusIntent.TECHNICAL_EXPLANATION, extracted_params

        # Y. Programming Help ("Help me write code", "Debug this code")
        if re.search(r'\b(code|write\s+a\s+program|debug|script|function|algorithm|binary\s+search|syntax)\b', text_lower):
            return NovusIntent.PROGRAMMING_HELP, extracted_params

        # Z. Task Continuation ("Continue", "Next", "Start week one", "Proceed")
        if re.search(r'^(continue|next|let\'?s\s+proceed|keep\s+going|start\s+week\s+one|start\s+phase\s+1|proceed)\b', text_lower):
            return NovusIntent.CONTINUE_PREVIOUS_TASK, extracted_params

        # AA. Acknowledgement ("OK", "Okay", "Got it", "Understood", "Cool", "Sure", "Right", "Fine")
        if re.search(r'^(ok|okay|k|got\s+it|understood|cool|sure|alright|fine|right|sounds\s+good|i\s+see|noted|perfect|great)\b', text_lower):
            return NovusIntent.ACKNOWLEDGEMENT, extracted_params

        # BB. Gratitude ("Thank you", "Thanks", "Appreciate it")
        if re.search(r'\b(thank\s+you|thanks|thx|thank\s+u|appreciate\s+it|much\s+appreciated|thanks\s+a\s+lot|thankyou)\b', text_lower):
            return NovusIntent.GRATITUDE, extracted_params

        # CC. Farewell ("Bye", "Goodbye", "See you")
        if re.search(r'\b(bye|goodbye|cya|see\s+ya|see\s+you|talk\s+to\s+you\s+later|take\s+care|catch\s+you\s+later|have\s+a\s+good\s+day)\b', text_lower):
            return NovusIntent.FAREWELL, extracted_params

        # DD. Greeting ("Hi", "Hello", "Hey", "Good morning", "What's up")
        if re.search(r'^(hi|hello|hey|heyy|heya|howdy|yo|greetings|good\s+(morning|afternoon|evening|day))\b', text_lower):
            return NovusIntent.GREETING, extracted_params

        # EE. Casual Conversation ("How are you?", "Who are you?", "What can you do?")
        if re.search(r'\b(how\s+are\s+you|who\s+are\s+you|what\s+is\s+your\s+name|what\s+can\s+you\s+do|tell\s+me\s+about\s+yourself)\b', text_lower):
            return NovusIntent.CASUAL_CONVERSATION, extracted_params

        # FF. Clarification Request ("What do you mean?", "I don't understand")
        if re.search(r'\b(what\s+do\s+you\s+mean|i\s+don\'?t\s+understand|can\s+you\s+clarify|could\s+you\s+clarify|explain\s+that\s+again|be\s+more\s+specific)\b', text_lower):
            return NovusIntent.CLARIFICATION, extracted_params

        # GG. Help Request ("Help", "I need help", "What can I ask you?")
        if re.search(r'^(help|help\s+me|i\s+need\s+help|guide\s+me|what\s+can\s+i\s+ask|how\s+does\s+this\s+work|show\s+options)\b', text_lower):
            return NovusIntent.HELP_REQUEST, extracted_params

        # HH. New Conversation / Reset
        if re.search(r'\b(start\s+over|reset\s+chat|new\s+conversation|clear\s+context|restart)\b', text_lower):
            return NovusIntent.NEW_CONVERSATION, extracted_params

        # II. Fallback to Gemini Semantic Intent Classification if online
        if gemini_client.is_configured:
            try:
                gemini_intent = cls._classify_with_gemini(text)
                if gemini_intent and gemini_intent != NovusIntent.UNKNOWN:
                    return gemini_intent, extracted_params
            except Exception as e:
                logger.warning(f"Gemini intent classification fallback failed: {e}")

        return NovusIntent.UNKNOWN, extracted_params

    @classmethod
    def _classify_with_gemini(cls, text: str) -> Optional[NovusIntent]:
        """Uses Gemini to classify non-obvious ambiguous user messages."""
        prompt = (
            f"Classify the intent of this student chat message in a campus career placement assistant into exactly ONE of these keys: "
            f"greeting, job_search, internship_search, career_guidance, learning_recommendation, "
            f"skill_gap_analysis, learning_roadmap, resume_analysis, mock_interview, acknowledgement, gratitude, help_request, unknown.\n\n"
            f"Message: \"{text}\"\n"
            f"Return ONLY the exact key name and nothing else."
        )
        res = gemini_client.generate_content(contents=prompt, temperature=0.1)
        if res.get('success') and res.get('text'):
            key = res['text'].strip().lower()
            for intent in NovusIntent:
                if intent.value == key:
                    return intent
        return None

    # -------------------------------------------------------------------------
    # 2. INTENT EXECUTION & RESPONSE GENERATION
    # -------------------------------------------------------------------------

    @classmethod
    def execute_and_respond(
        cls,
        intent: NovusIntent,
        student: StudentProfile,
        conversation: AIConversation,
        state: ConversationState,
        params: dict,
        message_text: str
    ) -> Tuple[Optional[dict], Optional[dict], str]:
        """
        Executes authorised backend operations for the identified intent,
        updates ConversationState, and returns: (structured_data, tool_log, response_text).
        """
        first_name = student.user.first_name or student.user.username
        branch = student.get_branch_display()
        cgpa = student.cgpa
        skills = [s.skill_name for s in student.skills.all()]
        skills_str = ", ".join(skills[:3]) if skills else "engineering core competencies"

        # ---------------------------------------------------------------------
        # INTENT: GREETING
        # ---------------------------------------------------------------------
        if intent == NovusIntent.GREETING:
            greetings = [
                f"Hey {first_name}! Good to see you. How is your {branch} semester going? What can I help you with today?",
                f"Hello {first_name}! Great to have you back. What would you like to explore or work on today?",
                f"Hi {first_name}! Hope you're having a productive day. How can I assist you with your career prep or placement goals?"
            ]
            # Pick a greeting that wasn't used in the immediate previous assistant message
            last_msg = conversation.messages.filter(role=AIMessage.Role.ASSISTANT).last()
            selected = greetings[0]
            if last_msg:
                for g in greetings:
                    if g[:15] not in last_msg.content:
                        selected = g
                        break
            return None, None, selected

        # ---------------------------------------------------------------------
        # INTENT: JOB SEARCH
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.JOB_SEARCH:
            kw = params.get('keyword', '')
            job_results = VEXToolService.find_matching_jobs(student=student, keyword=kw, limit=4)
            job_ids = [j['id'] for j in job_results['jobs']]

            state.active_intent = 'job_search'
            state.active_task = 'job_search_results'
            state.active_entity_type = 'job'
            state.active_entity_ids = job_ids
            state.last_tool_called = 'find_matching_jobs'
            state.last_tool_payload = job_results
            state.save()

            count = job_results['count']
            if count > 0:
                kw_str = f" for '{kw}'" if kw else ""
                response_text = (
                    f"I scanned the active openings on NexGrad matching your **{branch}** background (CGPA: {cgpa}) and skills in **{skills_str}**{kw_str}:\n\n"
                    f"I identified **{count} high-affinity job opportunities** currently accepting applications. "
                    f"Review the opportunity cards below, ask me to **'Show the first one'** for complete job specifications, or **'Apply for job 1'**."
                )
                return {'type': 'job_list', 'data': job_results}, {'tool': 'find_matching_jobs', 'keyword': kw}, response_text
            else:
                response_text = (
                    f"There are currently no active job requisitions matching '{kw}' specifically for {branch} students right now. "
                    f"However, new campus recruitment drives open regularly. In the meantime, would you like to **analyze your skill gaps** or **practice technical mock interview questions**?"
                )
                return None, {'tool': 'find_matching_jobs', 'keyword': kw}, response_text

        # ---------------------------------------------------------------------
        # INTENT: INTERNSHIP SEARCH
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.INTERNSHIP_SEARCH:
            intern_results = VEXToolService.find_matching_internships(student=student, limit=4)
            intern_ids = [i['id'] for i in intern_results['internships']]

            state.active_intent = 'find_internships'
            state.active_task = 'internship_search_results'
            state.active_entity_type = 'internship'
            state.active_entity_ids = intern_ids
            state.last_tool_payload = intern_results
            state.save()

            response_text = (
                f"Here are **{intern_results['count']} targeted internship programs** currently accepting student applications on NexGrad:\n\n"
                f"Each program listing displays your branch eligibility, duration, and monthly stipend. Explore the program cards below or ask me about any listing."
            )
            return {'type': 'internship_list', 'data': intern_results}, {'tool': 'find_matching_internships'}, response_text

        # ---------------------------------------------------------------------
        # INTENT: CAREER GUIDANCE & RECOMMENDATIONS
        # ---------------------------------------------------------------------
        elif intent in [NovusIntent.CAREER_GUIDANCE, NovusIntent.CAREER_RECOMMENDATION]:
            state.active_intent = 'career_guidance'
            state.save()

            top_skill = skills[0] if skills else "software engineering"
            response_text = (
                f"Based on your **{student.degree} in {branch}** (CGPA: **{cgpa}**) and hands-on skills in **{skills_str}**, here is my personalized career recommendation for you right now:\n\n"
                f"1. **Target Engineering Role:** With your background in {top_skill}, your strongest market positioning is for **Backend Systems Engineer** or **Full-Stack Software Engineer** roles.\n"
                f"2. **Critical Placement Priority:** Cloud deployment and containerization are the most decisive differentiators for campus hiring. Adding verified experience with **Docker** and **PostgreSQL/AWS** will immediately put your profile in the top bracket.\n"
                f"3. **Capstone Portfolio Evidence:** Build and deploy a multi-service web project with API documentation and automated tests on your GitHub.\n\n"
                f"Where would you like to focus right now? You can say:\n"
                f"- *'Is there any job?'* to see matching vacancies\n"
                f"- *'What should I learn next?'* to bridge missing skills\n"
                f"- *'Create a learning roadmap'* for a 12-week study plan"
            )
            return None, None, response_text

        # ---------------------------------------------------------------------
        # INTENT: ACKNOWLEDGEMENT ("OK", "Got it", "Cool")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.ACKNOWLEDGEMENT:
            if state.active_task == 'job_search_results' and state.active_entity_ids:
                return None, None, f"Sounds good, {first_name}! Whenever you're ready, say **'Show the first one'** to inspect full specifications, **'Compare the first and second jobs'**, or **'Apply for job 1'**."
            elif state.active_task == 'viewing_job_detail':
                return None, None, f"Understood! Would you like me to prepare an application for this role, or would you like to explore other listings?"
            elif state.active_task in ['learning_roadmap', 'viewing_roadmap_phase']:
                return None, None, f"Great! Work through the current roadmap milestones, and let me know when you're ready to advance to the next phase."
            elif state.active_task == 'interview_session':
                return None, None, f"Ready when you are! Type your response to the question above, or say **'Next question'** to proceed."
            else:
                return None, None, f"Sounds good, {first_name}! Let me know what you'd like to tackle next—whether that's searching for jobs, reviewing your resume, or practicing technical questions."

        # ---------------------------------------------------------------------
        # INTENT: GRATITUDE ("Thank you", "Thanks")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.GRATITUDE:
            responses = [
                f"You're very welcome, {first_name}! I'm always here to help you succeed in your career journey. Let me know whenever you need anything else.",
                f"Glad I could help, {first_name}! Keep up the great work and reach out anytime you have placement or technical questions.",
                f"Anytime, {first_name}! Best of luck with your preparation, and I'm right here if you need more guidance."
            ]
            return None, None, responses[0]

        # ---------------------------------------------------------------------
        # INTENT: FAREWELL ("Bye", "Goodbye")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.FAREWELL:
            return None, None, f"Goodbye, {first_name}! Best of luck with your studies and placement prep. Come back anytime you need guidance!"

        # ---------------------------------------------------------------------
        # INTENT: CASUAL CONVERSATION ("How are you?", "Who are you?")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.CASUAL_CONVERSATION:
            return None, None, (
                f"I'm doing great, thank you for asking! I'm **Novus**, your personal AI career companion at NexGrad. "
                f"I'm specifically tailored to understand your {branch} coursework, skills, and placement requirements to help you land the best possible engineering opportunities."
            )

        # ---------------------------------------------------------------------
        # INTENT: HELP REQUEST ("Help", "What can I ask you?")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.HELP_REQUEST:
            return None, None, (
                f"Here are the key ways I can help you as your NexGrad career companion, {first_name}:\n\n"
                f"- **Find Opportunities:** Say *'Is there any job?'* or *'Any internships available?'*\n"
                f"- **Career Guidance:** Say *'What should I do?'* or *'Which career is suitable for me?'*\n"
                f"- **Skill Gap Analysis:** Say *'Analyze my skill gaps for Backend Engineer'*\n"
                f"- **Learning Roadmaps:** Say *'Create a learning roadmap for Full Stack'*\n"
                f"- **Resume Audit:** Say *'Review my resume'* or *'Fix these issues'*\n"
                f"- **Mock Technical Interviews:** Say *'Start a mock interview'* or *'Next question'*\n\n"
                f"What would you like to work on right now?"
            )

        # ---------------------------------------------------------------------
        # INTENT: SHOW PREVIOUS RESULTS ("Show me", "Display results")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.SHOW_PREVIOUS_RESULTS:
            if state.active_entity_type == 'job' and state.active_entity_ids:
                res = VEXToolService.get_jobs_by_ids(student, state.active_entity_ids)
                active_ids = [j['id'] for j in res['jobs']]
                deactivated_count = len(state.active_entity_ids) - len(active_ids)
                state.active_entity_ids = active_ids
                state.save()

                if not res['jobs']:
                    return None, None, "The previously listed job opportunities have expired or are no longer active. Would you like me to scan for fresh matching jobs?"

                note = f"\n\n*(Note: {deactivated_count} position(s) recently closed or became inactive and were updated.)*" if deactivated_count > 0 else ""
                response_text = (
                    f"Here are the **{res['count']} matching opportunities** previously identified for your profile:{note}\n\n"
                    f"You can ask me to **'Show the first one'** to inspect full specs and responsibilities, **'Compare the first and second jobs'**, or **'Apply for the first one'**."
                )
                return {'type': 'job_list', 'data': res}, {'tool': 'get_jobs_by_ids', 'job_ids': active_ids}, response_text
            else:
                # Run fresh job search
                return cls.execute_and_respond(NovusIntent.JOB_SEARCH, student, conversation, state, params, message_text)

        # ---------------------------------------------------------------------
        # INTENT: JOB DETAILS ("Show the first one", "Explain this job")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.JOB_DETAILS:
            target_job_id = None
            job_num = 1
            if 'ordinal_idx' in params and state.active_entity_ids and params['ordinal_idx'] < len(state.active_entity_ids):
                idx = params['ordinal_idx']
                target_job_id = state.active_entity_ids[idx]
                job_num = idx + 1
            elif state.metadata.get('selected_job_id'):
                target_job_id = state.metadata['selected_job_id']
            elif state.active_entity_ids:
                target_job_id = state.active_entity_ids[0]

            if not target_job_id:
                return cls.execute_and_respond(NovusIntent.JOB_SEARCH, student, conversation, state, params, message_text)

            detail = VEXToolService.get_job_detail_by_id(student, target_job_id)
            if not detail:
                return None, None, "The requested job opening is no longer active in the NexGrad database. Would you like me to scan for fresh opportunities?"

            state.active_task = 'viewing_job_detail'
            state.metadata['selected_job_id'] = target_job_id
            state.metadata['selected_job_title'] = detail['title']
            state.metadata['selected_company'] = detail['company']
            state.save()

            already_str = " (You have already applied for this role)" if detail['is_already_applied'] else ""
            response_text = (
                f"Here are the complete specifications for **{detail['title']}** at **{detail['company']}** (Job #{job_num}){already_str}:\n\n"
                f"- **Workplace & Location:** {detail['location']} ({detail['workplace_type']})\n"
                f"- **Compensation Band:** {detail['salary_range']}\n"
                f"- **Academic Eligibility:** Min CGPA {detail['min_cgpa']} • Branches: {detail['eligible_branches']}\n"
                f"- **Your Affinity Score:** **{detail['match_percentage']}% Match** ({'Fully Eligible' if detail['is_fully_eligible'] else 'Check Branch/CGPA'})\n\n"
                f"**Key Responsibilities:**\n{detail['responsibilities'][:300]}...\n\n"
                f"Would you like me to prepare an application for this position? Simply reply **'Apply for this job'**."
            )
            return {'type': 'job_detail', 'data': detail}, {'tool': 'get_job_detail_by_id', 'job_id': target_job_id}, response_text

        # ---------------------------------------------------------------------
        # INTENT: JOB COMPARISON ("Compare the first and third jobs")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.JOB_COMPARISON:
            if not state.active_entity_ids or len(state.active_entity_ids) < 2:
                return None, None, "Please search for jobs first so I have listings to compare for you! Say **'Is there any job?'** to begin."

            idx1 = params.get('compare_idx1', 0)
            idx2 = params.get('compare_idx2', 1)
            idx1 = min(idx1, len(state.active_entity_ids) - 1)
            idx2 = min(idx2, len(state.active_entity_ids) - 1)
            if idx1 == idx2 and len(state.active_entity_ids) > 1:
                idx2 = 1 if idx1 == 0 else 0

            id1 = state.active_entity_ids[idx1]
            id2 = state.active_entity_ids[idx2]
            comp = VEXToolService.compare_jobs_by_ids(student, id1, id2)
            if not comp:
                return None, None, "Could not compare the selected jobs because one or both are no longer active."

            j1 = comp['job_1']
            j2 = comp['job_2']
            state.active_task = 'job_comparison'
            state.save()

            response_text = (
                f"Here is a side-by-side comparison of your selected opportunities:\n\n"
                f"| Metric | {j1['title']} ({j1['company']}) | {j2['title']} ({j2['company']}) |\n"
                f"|---|---|---|\n"
                f"| **Location** | {j1['location']} ({j1['workplace_type']}) | {j2['location']} ({j2['workplace_type']}) |\n"
                f"| **Compensation** | {j1['salary_range']} | {j2['salary_range']} |\n"
                f"| **Your Match** | **{j1['match_percentage']}%** | **{j2['match_percentage']}%** |\n"
                f"| **Eligibility** | {'Eligible' if j1['is_fully_eligible'] else 'Check Specs'} | {'Eligible' if j2['is_fully_eligible'] else 'Check Specs'} |\n\n"
                f"Both positions match your profile well. Would you like to apply for **{j1['title']}** or **{j2['title']}**?"
            )
            return {'type': 'job_comparison', 'data': comp}, {'tool': 'compare_jobs_by_ids'}, response_text

        # ---------------------------------------------------------------------
        # INTENT: JOB ELIGIBILITY ("Am I eligible?")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.JOB_ELIGIBILITY:
            job_id = state.metadata.get('selected_job_id') or (state.active_entity_ids[0] if state.active_entity_ids else None)
            if not job_id:
                return None, None, f"You don't currently have a job selected, {first_name}. Ask me **'Is there any job?'** and I'll verify your academic and technical eligibility across all active roles."

            detail = VEXToolService.get_job_detail_by_id(student, job_id)
            if not detail:
                return None, None, "The selected position is no longer active."

            elig_status = "Fully Eligible" if detail['is_fully_eligible'] else "Partial / Needs Review"
            response_text = (
                f"**Eligibility Breakdown for {detail['title']} at {detail['company']}:**\n\n"
                f"- **Your Status:** **{elig_status}**\n"
                f"- **CGPA Requirement:** Min {detail['min_cgpa']} (Your CGPA: **{cgpa}** — {'Passed' if detail['cgpa_eligible'] else 'Below Threshold'})\n"
                f"- **Branch Requirement:** {detail['eligible_branches']} (Your Branch: **{branch}** — {'Passed' if detail['branch_eligible'] else 'Check with Placement Cell'})\n"
                f"- **Skill Match:** **{detail['match_percentage']}%** compatible with your verified stack.\n\n"
                f"Would you like me to prepare your application draft? Say **'Apply for this job'**."
            )
            return {'type': 'job_detail', 'data': detail}, {'tool': 'get_job_detail_by_id', 'job_id': job_id}, response_text

        # ---------------------------------------------------------------------
        # INTENT: APPLY JOB
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.APPLY_JOB:
            target_job_id = None
            ref = params.get('ordinal_ref')
            if ref in ['this', 'it']:
                target_job_id = state.metadata.get('selected_job_id') or (state.active_entity_ids[0] if state.active_entity_ids else None)
            elif 'ordinal_idx' in params and state.active_entity_ids and params['ordinal_idx'] < len(state.active_entity_ids):
                target_job_id = state.active_entity_ids[params['ordinal_idx']]
            elif state.metadata.get('selected_job_id'):
                target_job_id = state.metadata['selected_job_id']
            elif state.active_entity_ids:
                target_job_id = state.active_entity_ids[0]

            if not target_job_id:
                return None, None, "Please select an active job first by saying **'Is there any job?'**"

            draft = VEXToolService.prepare_application_draft(student, target_job_id)
            if draft.get('is_already_applied'):
                return None, None, f"You have already applied for **{draft['job_title']}** at **{draft['company']}** (Current Status: **{draft['status']}** on {draft['applied_at']})."

            if 'error' in draft:
                return None, None, f"⚠️ {draft['error']}"

            state.active_task = 'awaiting_application_confirmation'
            state.metadata['target_job_id'] = target_job_id
            state.metadata['target_job_title'] = draft['job_title']
            state.metadata['target_company'] = draft['company']
            state.save()

            response_text = (
                f"I have prepared your application draft for **{draft['job_title']}** at **{draft['company']}**:\n\n"
                f"- **Resume Attached:** {draft['resume_title']}\n"
                f"- **Candidate:** {student.user.get_full_name() or student.user.username} ({branch}, CGPA: {cgpa})\n"
                f"- **Compensation:** {draft['salary_range']} • Location: {draft['location']}\n\n"
                f"**Please confirm:** Would you like me to submit your application now? Reply **'Confirm'** to submit or **'Cancel'** to review."
            )
            return {'type': 'application_confirmation', 'data': draft}, {'tool': 'prepare_application_draft'}, response_text

        # ---------------------------------------------------------------------
        # INTENT: CONFIRM ACTION
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.CONFIRM_ACTION:
            target_job_id = state.metadata.get('target_job_id')
            if not target_job_id:
                return None, None, "No active job application draft is currently pending confirmation."

            res = VEXToolService.confirm_and_submit_application(student, target_job_id)
            if not res['success']:
                return None, None, f"⚠️ {res['error']}"

            state.active_task = 'application_submitted'
            state.metadata['submitted_job_id'] = target_job_id
            state.save()

            response_text = (
                f"🎉 **Application Submitted Successfully!**\n\n"
                f"Your application for **{res['job_title']}** at **{res['company']}** has been officially registered on NexGrad.\n\n"
                f"Recruiter review updates will appear under your Applications tab. Would you like to practice mock interview questions for this role?"
            )
            return {'type': 'application_success', 'data': res}, {'tool': 'confirm_and_submit_application'}, response_text

        # ---------------------------------------------------------------------
        # INTENT: CANCEL ACTION
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.CANCEL_ACTION:
            state.active_task = 'job_search_results'
            state.save()
            return None, None, "Application draft cancelled. You can review other opportunities, compare roles, or continue your career prep."

        # ---------------------------------------------------------------------
        # INTENT: LEARNING RECOMMENDATION ("What should I learn next?")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.LEARNING_RECOMMENDATION:
            state.active_intent = 'learning_recommendation'
            state.save()

            response_text = (
                f"Looking at your verified skill profile ({skills_str}), the highest return-on-investment technologies for you to master next are:\n\n"
                f"1. **Containerization (Docker & Compose):** Industry standards require multi-container setups and isolated deployment environments.\n"
                f"2. **Production Relational Databases (PostgreSQL / Indexing):** Practice query profiling (`EXPLAIN ANALYZE`), composite indexes, and transaction isolation levels.\n"
                f"3. **In-Memory Caching (Redis):** Learn distributed cache patterns, rate-limiting algorithms, and session caching.\n\n"
                f"Would you like me to build a **12-week structured learning roadmap** to systematically master these topics?"
            )
            return None, None, response_text

        # ---------------------------------------------------------------------
        # INTENT: SKILL GAP ANALYSIS
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.SKILL_GAP_ANALYSIS:
            target_role = params.get('target_role') or 'Backend Engineer'
            gap_results = VEXToolService.analyse_skill_gaps(student=student, target_role=target_role)

            state.active_intent = 'skill_gap'
            state.active_task = 'skill_gap_review'
            state.active_entity_type = 'skill_gap'
            state.last_tool_called = 'analyse_skill_gaps'
            state.last_tool_payload = gap_results
            state.metadata['target_role'] = target_role
            state.save()

            response_text = (
                f"Here is your targeted **Skill Gap Analysis for {target_role.title()}**:\n\n"
                f"You currently match **{gap_results['readiness_score']}%** of active industry criteria. "
                f"I have broken down your verified competencies alongside critical missing technologies below.\n\n"
                f"Ask me **'How do I improve it?'** to get targeted project ideas and a study roadmap."
            )
            return {'type': 'skill_matrix', 'data': gap_results}, {'tool': 'analyse_skill_gaps', 'target_role': target_role}, response_text

        # ---------------------------------------------------------------------
        # INTENT: LEARNING ROADMAP
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.LEARNING_ROADMAP:
            target_role = params.get('target_role') or 'Full Stack Software Engineer'
            roadmap_results = VEXToolService.create_learning_roadmap(student=student, target_role=target_role, duration_weeks=12)

            state.active_intent = 'create_roadmap'
            state.active_task = 'learning_roadmap'
            state.active_entity_type = 'learning_plan'
            state.active_entity_ids = [roadmap_results['plan_id']]
            state.last_tool_called = 'create_learning_roadmap'
            state.last_tool_payload = roadmap_results
            state.metadata['target_role'] = target_role
            state.save()

            response_text = (
                f"I have constructed a comprehensive **12-Week Mastery Roadmap for {target_role.title()}** customized for you, {first_name}.\n\n"
                f"This plan is divided into 4 structured phases from core architectural fundamentals up to cloud deployment and capstone defense. "
                f"Say **'Start week one'** to inspect your first set of engineering tasks."
            )
            return {'type': 'learning_roadmap', 'data': roadmap_results}, {'tool': 'create_learning_roadmap', 'target_role': target_role}, response_text

        # ---------------------------------------------------------------------
        # INTENT: CONTINUE PREVIOUS TASK ("Continue", "Start week one")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.CONTINUE_PREVIOUS_TASK:
            plan = student.learning_plans.filter(is_active=True).first()
            if plan and plan.phases:
                phase1 = plan.phases[0]
                state.active_task = 'viewing_roadmap_phase'
                state.save()

                tasks_str = "\n".join([f"- [ ] {t['title']}" for t in phase1.get('tasks', [])])
                response_text = (
                    f"**Phase 1: {phase1.get('title')} ({phase1.get('duration')})**\n\n"
                    f"{phase1.get('description')}\n\n"
                    f"**Actionable Tasks:**\n{tasks_str}\n\n"
                    f"**Capstone Milestone:** {phase1.get('project_milestone')}\n\n"
                    f"Once you complete these tasks, let me know and we'll advance to Phase 2!"
                )
                return {'type': 'roadmap_phase_detail', 'data': phase1}, None, response_text
            else:
                return cls.execute_and_respond(NovusIntent.LEARNING_ROADMAP, student, conversation, state, params, message_text)

        # ---------------------------------------------------------------------
        # INTENT: RESUME ANALYSIS
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.RESUME_ANALYSIS:
            target_role = params.get('target_role') or 'Software Engineer'
            resume_results = VEXToolService.analyse_resume(student=student, target_role=target_role)

            state.active_intent = 'analyse_resume'
            state.active_task = 'resume_analysis'
            state.active_entity_type = 'resume'
            state.active_entity_ids = [resume_results['analysis_id']]
            state.last_tool_called = 'analyse_resume'
            state.last_tool_payload = resume_results
            state.metadata['target_role'] = target_role
            state.save()

            response_text = (
                f"Here is your **Resume & Profile Audit for {target_role}**:\n\n"
                f"I evaluated your coursework, listed projects, and skill tags. "
                f"Below are key strengths to highlight and high-impact gaps to address.\n\n"
                f"Ask me **'Fix these issues'** to see rewritten Google XYZ bullet points for your projects."
            )
            return {'type': 'resume_analysis', 'data': resume_results}, {'tool': 'analyse_resume', 'target_role': target_role}, response_text

        # ---------------------------------------------------------------------
        # INTENT: RESUME IMPROVEMENT ("Fix these issues")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.RESUME_IMPROVEMENT:
            payload = state.last_tool_payload or {}
            target_role = payload.get('target_role') or 'Software Engineer'

            state.active_task = 'resume_rewrite_guidance'
            state.save()

            response_text = (
                f"Here is how to rewrite your project descriptions using the **Google XYZ Formula** ('Accomplished [X] as measured by [Y], by doing [Z]'):\n\n"
                f"**Example Project Bullet Rewrite:**\n"
                f"- *Before:* 'Built a backend web API in Django with database support.'\n"
                f"- *After:* 'Architected a multi-tenant REST API with Django and PostgreSQL, achieving sub-45ms P99 query latency by designing composite B-Tree indexes and implementing Redis caching.'\n\n"
                f"**Tailored Professional Summary for {target_role}:**\n"
                f"> \"{payload.get('suggested_summary', 'Driven engineering student with verified skills in scalable software systems.')}\"\n\n"
                f"You can copy this summary directly into your resume header!"
            )
            return {'type': 'resume_rewrite_advice', 'data': payload}, None, response_text

        # ---------------------------------------------------------------------
        # INTENT: MOCK INTERVIEW
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.MOCK_INTERVIEW:
            target_role = params.get('target_role') or state.metadata.get('target_role', 'Software Engineer')
            session_id = params.get('session_id') or (state.active_entity_ids[0] if (state.active_entity_type == 'mock_interview' and state.active_entity_ids) else None)
            student_resp = params.get('student_response')

            interview_result = VEXToolService.conduct_mock_interview(
                student=student,
                target_role=target_role,
                interview_type='TECHNICAL',
                student_response=student_resp,
                session_id=session_id
            )

            state.active_intent = 'mock_interview'
            state.active_task = 'interview_session'
            state.active_entity_type = 'mock_interview'
            state.active_entity_ids = [interview_result['session_id']]
            state.last_tool_called = 'conduct_mock_interview'
            state.last_tool_payload = interview_result
            state.metadata['target_role'] = target_role
            state.save()

            if interview_result.get('is_finished'):
                response_text = (
                    f"🎉 **Mock Interview Completed!**\n\n"
                    f"**Overall Rating:** {interview_result.get('overall_score')}/10.\n\n"
                    f"{interview_result.get('summary')}"
                )
            else:
                q_num = interview_result.get('question_number', 1)
                q_text = interview_result.get('question_text', '')
                feedback_lead = ""
                if interview_result.get('last_feedback'):
                    last_f = interview_result['last_feedback']
                    feedback_lead = f"**Previous Answer Evaluation:** Score {last_f['score']}/10.\n*{last_f['feedback']}*\n\n---\n\n"

                response_text = (
                    f"{feedback_lead}**Mock Interview — Question {q_num} of {interview_result.get('total_questions', 3)}**:\n\n"
                    f"> {q_text}\n\n"
                    f"Type your answer directly in the box below to receive instant rubric scoring."
                )

            return {'type': 'mock_interview', 'data': interview_result}, {'tool': 'conduct_mock_interview'}, response_text

        # ---------------------------------------------------------------------
        # INTENT: APPLICATION STATUS
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.APPLICATION_STATUS:
            res = VEXToolService.get_application_status(student=student)
            state.active_intent = 'application_status'
            state.active_task = 'viewing_applications'
            state.last_tool_called = 'get_application_status'
            state.save()
            return {'type': 'applications_summary', 'data': res}, {'tool': 'get_application_status'}, None

        # ---------------------------------------------------------------------
        # INTENT: TECHNICAL EXPLANATION ("Explain Redis", "What is indexing?")
        # ---------------------------------------------------------------------
        elif intent == NovusIntent.TECHNICAL_EXPLANATION:
            concept = params.get('concept', 'Systems Architecture').title()
            response_text = (
                f"**Technical Deep-Dive: {concept}**\n\n"
                f"In enterprise engineering systems, **{concept}** is essential for high availability and low latency:\n\n"
                f"- **Core Concept:** It enables distributed components to decouple execution, cache hot reads, or optimize lookups from O(N) disk scans down to O(log N) memory access.\n"
                f"- **Production Trade-Offs:** Consider write amplification, cache-invalidation challenges, and memory footprint versus raw throughput.\n"
                f"- **Interview Talking Point:** In technical interviews, always frame {concept} by discussing baseline constraints, failure modes, and P99 latency guarantees."
            )
            return None, None, response_text

        # ---------------------------------------------------------------------
        # INTENT: CLARIFICATION / UNKNOWN
        # ---------------------------------------------------------------------
        else:
            # Focused clarification question instead of dumping a menu
            return None, None, (
                f"I want to make sure I understand you properly, {first_name}. "
                f"Are you looking to search active jobs, get career advice for {branch}, review your resume, or practice mock interview questions?"
            )

