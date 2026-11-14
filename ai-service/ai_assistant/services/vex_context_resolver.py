import re
from typing import Dict, Any, Optional, Tuple, List
from students.models import StudentProfile
from ai_assistant.models import AIConversation, ConversationState, StudentLearningPlan
from .vex_tools import VEXToolService


class VEXContextResolver:
    """
    Context-aware intent and follow-up resolver for Novus.
    Interprets user messages within the persistent conversation state,
    resolving short follow-ups (e.g. 'Show me', 'Show the first one',
    'Apply for the second one', 'How do I improve it?') using real database entities.
    """

    ORDINAL_MAP = {
        'first': 0, '1st': 0, '1': 0, 'one': 0,
        'second': 1, '2nd': 1, '2': 1, 'two': 1,
        'third': 2, '3rd': 2, '3': 2, 'three': 2,
        'fourth': 3, '4th': 3, '4': 3, 'four': 3,
    }

    @classmethod
    def resolve_turn(
        cls,
        student: StudentProfile,
        message_text: str,
        conversation: AIConversation,
        action: Optional[str] = None,
        params: Optional[dict] = None
    ) -> Tuple[Optional[dict], Optional[dict], Optional[str]]:
        """
        Evaluates active state and message text.
        Returns: (structured_data, tool_log, resolved_response_text)
        """
        state = conversation.current_state
        text = (message_text or '').strip()
        text_lower = text.lower()
        clean_text = re.sub(r'[\.\?\!\,\;]+$', '', text_lower).strip()
        params = params or {}

        # ---------------------------------------------------------------------
        # 1. EXPLICIT UI ACTIONS
        # ---------------------------------------------------------------------
        if action == 'find_jobs':
            return cls._handle_find_jobs(student, state, keyword=params.get('keyword', ''))

        elif action == 'find_internships':
            return cls._handle_find_internships(student, state)

        elif action == 'skill_gap':
            target_role = params.get('target_role') or 'Backend Engineer'
            return cls._handle_skill_gap(student, state, target_role)

        elif action == 'create_roadmap':
            target_role = params.get('target_role') or 'Full Stack Software Engineer'
            return cls._handle_create_roadmap(student, state, target_role)

        elif action == 'mock_interview':
            target_role = params.get('target_role') or 'Software Engineer'
            return cls._handle_mock_interview(student, state, target_role, session_id=params.get('session_id'), student_response=params.get('student_response'))

        elif action == 'analyse_resume':
            target_role = params.get('target_role') or 'Software Engineer'
            return cls._handle_analyse_resume(student, state, target_role)

        elif action == 'confirm_application':
            job_id = params.get('job_id') or state.metadata.get('target_job_id')
            return cls._handle_confirm_application(student, state, job_id)

        # ---------------------------------------------------------------------
        # 2. CONTEXTUAL FOLLOW-UPS BASED ON ACTIVE STATE
        # ---------------------------------------------------------------------

        # A. Awaiting application submission confirmation
        if state.active_task == 'awaiting_application_confirmation':
            if re.search(r'\b(yes|confirm|submit|apply|go ahead|proceed|sure|yep|do it|ok)\b', text_lower):
                target_job_id = state.metadata.get('target_job_id')
                return cls._handle_confirm_application(student, state, target_job_id)
            elif re.search(r'\b(no|cancel|stop|don\'t|wait|abort|nevermind)\b', text_lower):
                state.active_task = 'job_search_results'
                state.save()
                return None, None, "Application draft cancelled. You can review other opportunities, compare roles, or continue your career prep."

        # B. Apply for job: "Apply for the second one" / "Apply to this job"
        apply_match = re.search(
            r'\bapply\s+(?:for|to)?\s+(?:the\s+)?(first|1st|1|second|2nd|2|third|3rd|3|fourth|4th|4|this|it)\b',
            text_lower
        )
        if apply_match and state.active_entity_type == 'job':
            ref = apply_match.group(1).lower()
            target_job_id = None
            if ref in ['this', 'it']:
                target_job_id = state.metadata.get('selected_job_id') or (state.active_entity_ids[0] if state.active_entity_ids else None)
            else:
                idx = cls.ORDINAL_MAP.get(ref)
                if idx is not None and state.active_entity_ids and idx < len(state.active_entity_ids):
                    target_job_id = state.active_entity_ids[idx]

            if target_job_id:
                return cls._handle_prepare_application(student, state, target_job_id)

        # C. Compare two jobs: "Compare the first and third jobs"
        compare_match = re.search(
            r'\bcompare\s+(?:the\s+)?(first|1st|1|second|2nd|2|third|3rd|3|fourth|4th|4)\s+(?:and|with|to)\s+(?:the\s+)?(first|1st|1|second|2nd|2|third|3rd|3|fourth|4th|4)\b',
            text_lower
        )
        if compare_match and state.active_entity_type == 'job' and state.active_entity_ids:
            w1 = compare_match.group(1).lower()
            w2 = compare_match.group(2).lower()
            idx1 = cls.ORDINAL_MAP.get(w1)
            idx2 = cls.ORDINAL_MAP.get(w2)
            if idx1 is not None and idx2 is not None and idx1 < len(state.active_entity_ids) and idx2 < len(state.active_entity_ids):
                id1 = state.active_entity_ids[idx1]
                id2 = state.active_entity_ids[idx2]
                return cls._handle_compare_jobs(student, state, id1, id2)

        # D. Show specific job by ordinal or "Explain this job" / "Tell me more"
        job_detail_match = re.search(
            r'\b(?:show|tell me about|details on|view|open|what about|describe|explain)\s+(?:the\s+)?(first|1st|1|second|2nd|2|third|3rd|3|fourth|4th|4|one|two|three|four)\b',
            clean_text
        ) or (not re.search(r'\bapply\b', clean_text) and re.search(
            r'\b(first|1st|second|2nd|third|3rd|fourth|4th)\s+(?:one|job|role|position|vacancy)\b',
            clean_text
        )) or re.search(
            r'\b(explain\s+(?:this\s+)?(?:job|role|position)|tell\s+me\s+more(?:\s+about\s+(?:this\s+)?(?:job|role|position))?|job\s+details|details\s+(?:on|about)\s+(?:this\s+)?(?:job|role))\b',
            clean_text
        ) or (state and state.active_entity_type == 'job' and clean_text in ['tell me more', 'details', 'explain'])
        if job_detail_match and state.active_entity_type == 'job' and state.active_entity_ids:
            word = None
            if hasattr(job_detail_match, 'group') and job_detail_match.lastindex:
                word = job_detail_match.group(1).lower()
            idx = cls.ORDINAL_MAP.get(word, 0) if word in cls.ORDINAL_MAP else 0
            if idx < len(state.active_entity_ids):
                target_job_id = state.metadata.get('selected_job_id') or state.active_entity_ids[idx]
                return cls._handle_view_job_detail(student, state, target_job_id, job_number=idx + 1)

        # E. Job search results follow-up: "Show me" / "Show them" / "Let me see"
        if re.search(r'^(show me|show them|show results|display them|let me see|can you show|view jobs|view results|see them|show all)(\s+(jobs|results|openings|opportunities))?$', clean_text) or clean_text in ['show', 'show me', 'show them', 'show all', 'display all']:
            if state.active_entity_type == 'job' and state.active_entity_ids:
                return cls._handle_show_previous_jobs(student, state)
            elif state.active_task == 'awaiting_job_search_approval':
                return cls._handle_find_jobs(student, state)

        # F. More jobs: "Are there any more?" / "Show more jobs"
        if re.search(r'\b(more jobs|additional jobs|show more|any more|next jobs|other jobs)\b', text_lower):
            if state.active_entity_type == 'job':
                return cls._handle_more_jobs(student, state)

        # G. Job Consultation: "Can you suggest me the best suitable job?"
        if re.search(r'\b(suggest\s+(?:me\s+)?(?:a\s+)?(?:suitable\s+|best\s+)?job|what\s+job|suitable\s+job|recommend\s+(?:a\s+)?job)\b', text_lower):
            return cls._handle_job_consultation(student, state)

        # H. Trigger job search if user asks directly or confirms consultation
        if re.search(
            r'\b(is\s+there\s+any\s+jobs?|are\s+there\s+(?:any\s+)?jobs?|any\s+jobs?|find\s+jobs?|search\s+jobs?|job\s+search|job\s+openings?|job\s+vacancies|suitable\s+vacancies|opportunities\s+for\s+me|jobs\s+for\s+me|what\s+jobs|available\s+jobs|show\s+(?:me\s+)?jobs|jobs\s+matching|find\s+matching\s+jobs|eligible\s+jobs|matching\s+jobs)\b',
            text_lower
        ) or text_lower in ['jobs', 'job', 'find job', 'find jobs', 'search job'] or (
            state.active_task == 'awaiting_job_search_approval' and re.search(r'\b(yes|sure|find|search|match|go ahead)\b', text_lower)
        ):
            return cls._handle_find_jobs(student, state)

        # I. Skill Gap Follow-up: "How do I improve it?" / "Fix gaps"
        if (state.active_intent == 'skill_gap' or state.active_task == 'skill_gap_review') and re.search(
            r'\b(how\s+do\s+i\s+improve|how\s+to\s+improve|improve\s+it|fix\s+gaps|what\s+should\s+i\s+do|how\s+to\s+learn|how\s+can\s+i\s+learn)\b',
            text_lower
        ):
            return cls._handle_skill_gap_advice(student, state)

        # J. Learning Roadmap Follow-up: "Start week one" / "Show phase 1" / "Continue"
        if (state.active_entity_type == 'learning_plan' or state.active_intent == 'create_roadmap') and re.search(
            r'\b(start\s+week\s+one|phase\s+1|week\s+1|continue|let\'s\s+begin|next\s+step)\b',
            text_lower
        ):
            return cls._handle_roadmap_phase_view(student, state)

        # K. Resume Follow-up: "Fix these issues" / "Improve it"
        if (state.active_intent == 'analyse_resume' or state.active_task == 'resume_analysis') and re.search(
            r'\b(fix\s+(?:these\s+)?issues|improve\s+it|how\s+to\s+fix|rewrite\s+bullets|fix\s+resume)\b',
            text_lower
        ):
            return cls._handle_resume_rewrite_advice(student, state)

        # L. Mock Interview: "Next question"
        if state.active_task == 'interview_session' and re.search(r'\b(next\s+question|continue\s+interview)\b', text_lower):
            target_role = state.metadata.get('target_role', 'Software Engineer')
            session_id = state.active_entity_ids[0] if state.active_entity_ids else None
            return cls._handle_mock_interview(student, state, target_role, session_id=session_id)

        # M. Assessment: "Explain my mistakes" / "Review test"
        if re.search(r'\b(explain\s+my\s+mistakes|why\s+did\s+i\s+fail|review\s+assessment|mistakes|my\s+score)\b', text_lower):
            return cls._handle_assessment_review(student, state)

        # N. Standard direct intents: Skill Gap, Roadmap, Resume, Applications
        if any(k in text_lower for k in ['skill gap', 'missing skill', 'gap analysis']):
            target_role = 'Backend Engineer'
            m = re.search(r'(?:for|as a|become a)\s+([a-zA-Z\s]{3,25})', text_lower)
            if m:
                target_role = m.group(1).strip()
            return cls._handle_skill_gap(student, state, target_role)

        if any(k in text_lower for k in ['roadmap', 'learning plan', 'study plan', 'curriculum', 'how to prepare']):
            target_role = 'Full Stack Software Engineer'
            m = re.search(r'(?:for|to become|as a)\s+([a-zA-Z\s]{3,25})', text_lower)
            if m:
                target_role = m.group(1).strip()
            return cls._handle_create_roadmap(student, state, target_role)

        if any(k in text_lower for k in ['resume', 'cv', 'review my profile', 'ats score', 'improve resume']):
            return cls._handle_analyse_resume(student, state, 'Software Engineer')

        if any(k in text_lower for k in ['my application', 'applied status', 'application status', 'where did i apply']):
            res = VEXToolService.get_application_status(student=student)
            state.active_intent = 'application_status'
            state.active_task = 'viewing_applications'
            state.last_tool_called = 'get_application_status'
            state.save()
            return {'type': 'applications_summary', 'data': res}, {'tool': 'get_application_status'}, None

        # ---------------------------------------------------------------------
        # 3. ROUTE THROUGH ADVANCED INTENT ROUTER
        # ---------------------------------------------------------------------
        from .vex_intent_router import VEXIntentRouter
        intent, extracted_params = VEXIntentRouter.classify_intent(
            message_text=message_text,
            student=student,
            state=state,
            action=action,
            params=params
        )
        return VEXIntentRouter.execute_and_respond(
            intent=intent,
            student=student,
            conversation=conversation,
            state=state,
            params=extracted_params,
            message_text=message_text
        )

    # =========================================================================
    # INTERNAL HANDLERS
    # =========================================================================

    @classmethod
    def _handle_find_jobs(cls, student: StudentProfile, state: ConversationState, keyword: str = ''):
        job_results = VEXToolService.find_matching_jobs(student=student, keyword=keyword, limit=4)
        job_ids = [j['id'] for j in job_results['jobs']]

        state.active_intent = 'find_matching_jobs'
        state.active_task = 'job_search_results'
        state.active_entity_type = 'job'
        state.active_entity_ids = job_ids
        state.last_tool_called = 'find_matching_jobs'
        state.last_tool_payload = job_results
        state.context_summary = f"Retrieved {len(job_ids)} jobs matching student profile."
        state.save()

        count = job_results['count']
        response_text = (
            f"I have scanned the active job requisitions on NexGrad against your {student.get_branch_display()} background (CGPA: {student.cgpa}).\n\n"
            f"I identified **{count} high-compatibility opportunities** matching your coursework and technical skills. "
            f"You can explore the interactive opportunity cards below, say **'Show the first one'** for full specs, or **'Apply for job 1'**."
        )
        return {'type': 'job_list', 'data': job_results}, {'tool': 'find_matching_jobs', 'keyword': keyword}, response_text

    @classmethod
    def _handle_show_previous_jobs(cls, student: StudentProfile, state: ConversationState):
        job_ids = state.active_entity_ids or []
        res = VEXToolService.get_jobs_by_ids(student, job_ids)

        # Update active entity IDs to those still active
        active_ids = [j['id'] for j in res['jobs']]
        deactivated_count = len(job_ids) - len(active_ids)
        state.active_entity_ids = active_ids
        state.active_task = 'job_search_results'
        state.save()

        if not res['jobs']:
            return None, None, "The previously listed job opportunities have expired or are no longer active. Would you like me to scan for fresh matching jobs?"

        note = f"\n\n*(Note: {deactivated_count} position(s) recently closed or became inactive and were updated.)*" if deactivated_count > 0 else ""
        response_text = (
            f"Here are the **{res['count']} matching opportunities** previously identified for your profile:{note}\n\n"
            f"You can ask me to **'Show the first one'** to inspect full specs and responsibilities, **'Compare the first and second jobs'**, or **'Apply for the first one'**."
        )
        return {'type': 'job_list', 'data': res}, {'tool': 'get_jobs_by_ids', 'job_ids': active_ids}, response_text

    @classmethod
    def _handle_view_job_detail(cls, student: StudentProfile, state: ConversationState, job_id: int, job_number: int = 1):
        detail = VEXToolService.get_job_detail_by_id(student, job_id)
        if not detail:
            return None, None, "The requested job opening is no longer active in the NexGrad database. Would you like me to scan for fresh opportunities?"

        state.active_task = 'viewing_job_detail'
        state.metadata['selected_job_id'] = job_id
        state.metadata['selected_job_title'] = detail['title']
        state.metadata['selected_company'] = detail['company']
        state.save()

        already_str = " (You have already applied for this role)" if detail['is_already_applied'] else ""
        response_text = (
            f"Here are the complete specifications for **{detail['title']}** at **{detail['company']}** (Job #{job_number}){already_str}:\n\n"
            f"- **Workplace & Location:** {detail['location']} ({detail['workplace_type']})\n"
            f"- **Compensation Band:** {detail['salary_range']}\n"
            f"- **Academic Eligibility:** Min CGPA {detail['min_cgpa']} • Branches: {detail['eligible_branches']}\n"
            f"- **Your Affinity Score:** **{detail['match_percentage']}% Match** ({'Fully Eligible' if detail['is_fully_eligible'] else 'Check Branch/CGPA'})\n\n"
            f"**Key Responsibilities:**\n{detail['responsibilities'][:300]}...\n\n"
            f"Would you like me to prepare an application for this position? Simply reply **'Apply for this job'**."
        )
        return {'type': 'job_detail', 'data': detail}, {'tool': 'get_job_detail_by_id', 'job_id': job_id}, response_text

    @classmethod
    def _handle_compare_jobs(cls, student: StudentProfile, state: ConversationState, id1: int, id2: int):
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

    @classmethod
    def _handle_more_jobs(cls, student: StudentProfile, state: ConversationState):
        current_ids = state.active_entity_ids or []
        res = VEXToolService.find_matching_jobs(student=student, limit=6)
        # Exclude already shown jobs if possible
        new_jobs = [j for j in res['jobs'] if j['id'] not in current_ids]
        if not new_jobs:
            new_jobs = res['jobs'][:4]

        new_ids = [j['id'] for j in new_jobs]
        state.active_entity_ids = current_ids + new_ids
        state.active_task = 'job_search_results'
        state.last_tool_payload = {'jobs': new_jobs, 'count': len(new_jobs)}
        state.save()

        response_text = (
            f"I retrieved **{len(new_jobs)} additional opportunities** matching your background:\n\n"
            f"Review the new listings below or let me know which one you'd like to inspect in detail."
        )
        return {'type': 'job_list', 'data': {'jobs': new_jobs, 'count': len(new_jobs)}}, {'tool': 'find_matching_jobs'}, response_text

    @classmethod
    def _handle_prepare_application(cls, student: StudentProfile, state: ConversationState, job_id: int):
        draft = VEXToolService.prepare_application_draft(student, job_id)
        if draft.get('is_already_applied'):
            return None, None, f"You have already applied for **{draft['job_title']}** at **{draft['company']}** (Current Status: **{draft['status']}** on {draft['applied_at']})."

        if 'error' in draft:
            return None, None, f"⚠️ {draft['error']}"

        state.active_task = 'awaiting_application_confirmation'
        state.metadata['target_job_id'] = job_id
        state.metadata['target_job_title'] = draft['job_title']
        state.metadata['target_company'] = draft['company']
        state.save()

        response_text = (
            f"I have prepared your application draft for **{draft['job_title']}** at **{draft['company']}**:\n\n"
            f"- **Resume Attached:** {draft['resume_title']}\n"
            f"- **Candidate:** {student.user.get_full_name() or student.user.username} ({student.get_branch_display()}, CGPA: {student.cgpa})\n"
            f"- **Compensation:** {draft['salary_range']} • Location: {draft['location']}\n\n"
            f"**Please confirm:** Would you like me to submit your application now? Reply **'Confirm'** to submit or **'Cancel'** to review."
        )
        return {'type': 'application_confirmation', 'data': draft}, {'tool': 'prepare_application_draft'}, response_text

    @classmethod
    def _handle_confirm_application(cls, student: StudentProfile, state: ConversationState, job_id: Optional[int]):
        if not job_id:
            return None, None, "No active job application was selected. Please select a job to apply."

        res = VEXToolService.confirm_and_submit_application(student, job_id)
        if not res['success']:
            return None, None, f"⚠️ {res['error']}"

        state.active_task = 'application_submitted'
        state.metadata['submitted_job_id'] = job_id
        state.save()

        response_text = (
            f"🎉 **Application Submitted Successfully!**\n\n"
            f"Your application for **{res['job_title']}** at **{res['company']}** has been officially registered on NexGrad.\n\n"
            f"Recruiter review updates will appear under your Applications tab. Would you like to practice mock interview questions for this role?"
        )
        return {'type': 'application_success', 'data': res}, {'tool': 'confirm_and_submit_application'}, response_text

    @classmethod
    def _handle_job_consultation(cls, student: StudentProfile, state: ConversationState):
        state.active_intent = 'find_matching_jobs'
        state.active_task = 'awaiting_job_search_approval'
        state.active_entity_type = 'job'
        state.save()

        skills = [s.skill_name for s in student.skills.all()[:3]]
        skills_str = ", ".join(skills) if skills else "engineering foundations"
        response_text = (
            f"Based on your **{student.degree} in {student.get_branch_display()}** (CGPA: **{student.cgpa}**) and hands-on skills in **{skills_str}**, "
            f"you align well with software engineering and systems opportunities.\n\n"
            f"Would you like me to retrieve the active matching opportunities from the NexGrad database now? "
            f"You can say **'Show me'** or click **'Match Jobs'**."
        )
        return {'type': 'consultation_prompt', 'data': {'options': ['Find Matching Jobs & Internships', 'Analyze My Skill Gaps', 'Generate 12-Week Roadmap']}}, None, response_text

    @classmethod
    def _handle_find_internships(cls, student: StudentProfile, state: ConversationState):
        intern_results = VEXToolService.find_matching_internships(student=student, limit=4)
        intern_ids = [i['id'] for i in intern_results['internships']]

        state.active_intent = 'find_internships'
        state.active_task = 'internship_search_results'
        state.active_entity_type = 'internship'
        state.active_entity_ids = intern_ids
        state.last_tool_payload = intern_results
        state.save()

        response_text = (
            f"Here are **{intern_results['count']} targeted internship programs** currently active on NexGrad, {student.user.first_name or student.user.username}.\n\n"
            f"Each listing shows your current skill affinity match and compensation stipend. Check the program cards below."
        )
        return {'type': 'internship_list', 'data': intern_results}, {'tool': 'find_matching_internships'}, response_text

    @classmethod
    def _handle_skill_gap(cls, student: StudentProfile, state: ConversationState, target_role: str):
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

    @classmethod
    def _handle_skill_gap_advice(cls, student: StudentProfile, state: ConversationState):
        payload = state.last_tool_payload or {}
        missing = payload.get('missing_skills', [])
        target_role = payload.get('target_role') or state.metadata.get('target_role', 'Software Engineer')

        state.active_task = 'skill_gap_advice'
        state.save()

        missing_names = [m['name'] for m in missing[:3]] if missing else ['Docker', 'REST APIs', 'PostgreSQL']
        response_text = (
            f"To bridge your skill gaps for **{target_role}** ({', '.join(missing_names)}):\n\n"
            f"1. **Containerization & CI/CD:** Build a Dockerfile for a multi-service web app and configure GitHub Actions for automated testing.\n"
            f"2. **Production Schemas:** Implement relational database indexing, composite foreign keys, and query optimization.\n"
            f"3. **Capstone Portfolio Evidence:** Package these into a deployable open-source repo with an architectural README.\n\n"
            f"Would you like me to generate a complete **12-Week Accelerated Roadmap** to master these skills systematically?"
        )
        return {'type': 'skill_improvement_advice', 'data': {'target_role': target_role, 'missing_skills': missing}}, None, response_text

    @classmethod
    def _handle_create_roadmap(cls, student: StudentProfile, state: ConversationState, target_role: str):
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
            f"I have constructed a comprehensive **12-Week Mastery Roadmap for {target_role.title()}** customized for you.\n\n"
            f"This plan is divided into 4 structured phases from core architectural fundamentals up to cloud deployment and capstone defense. "
            f"Say **'Start week one'** to inspect your first set of engineering tasks."
        )
        return {'type': 'learning_roadmap', 'data': roadmap_results}, {'tool': 'create_learning_roadmap', 'target_role': target_role}, response_text

    @classmethod
    def _handle_roadmap_phase_view(cls, student: StudentProfile, state: ConversationState):
        plan = student.learning_plans.filter(is_active=True).first()
        if not plan or not plan.phases:
            return cls._handle_create_roadmap(student, state, 'Full Stack Software Engineer')

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

    @classmethod
    def _handle_analyse_resume(cls, student: StudentProfile, state: ConversationState, target_role: str):
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

    @classmethod
    def _handle_resume_rewrite_advice(cls, student: StudentProfile, state: ConversationState):
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

    @classmethod
    def _handle_mock_interview(cls, student: StudentProfile, state: ConversationState, target_role: str, session_id=None, student_response=None):
        interview_result = VEXToolService.conduct_mock_interview(
            student=student,
            target_role=target_role,
            interview_type='TECHNICAL',
            student_response=student_response,
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

    @classmethod
    def _handle_assessment_review(cls, student: StudentProfile, state: ConversationState):
        res = VEXToolService.get_assessment_results(student)
        state.active_intent = 'assessment_review'
        state.active_task = 'viewing_assessments'
        state.save()

        attempts = res.get('assessments', [])
        if not attempts:
            response_text = "You have not completed any formal technical assessments on NexGrad yet. Would you like to take one to verify your technical profile?"
        else:
            scores_str = "\n".join([f"- **{a['title']}**: {a['score']}% ({'Passed' if a['is_passed'] else 'Retake Recommended'})" for a in attempts[:3]])
            response_text = (
                f"Here is your recent technical assessment performance:\n\n"
                f"{scores_str}\n\n"
                f"To strengthen recruiter visibility, focus on retaking categories where your score fell below the passing threshold."
            )
        return {'type': 'assessment_summary', 'data': res}, {'tool': 'get_assessment_results'}, response_text
