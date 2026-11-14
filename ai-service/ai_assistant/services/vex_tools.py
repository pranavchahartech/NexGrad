import re
from typing import Dict, Any, List, Optional
from django.db.models import Q
from django.utils import timezone
from students.models import StudentProfile, StudentSkill, Project, Resume
from jobs.models import Job, Internship, Skill
from applications.models import Application
from assessments.models import AssessmentAttempt
from challenges.models import ChallengeAssignment
from ai_assistant.models import (
    StudentLearningPlan,
    LearningPlanProgress,
    InterviewSession,
    InterviewQuestion,
    ResumeAnalysis,
    StudentCareerGoal
)


class VEXToolService:
    """
    Executes controlled, authorized database actions and analytical tools
    for VEX. Strict student-level data isolation is enforced on every call.
    """

    @classmethod
    def get_student_profile(cls, student: StudentProfile) -> Dict[str, Any]:
        user = student.user
        return {
            'student_id': student.id,
            'name': user.get_full_name() or user.username,
            'branch': student.get_branch_display(),
            'degree': student.degree,
            'graduation_year': student.graduation_year,
            'cgpa': float(student.cgpa) if student.cgpa else 0.0,
            'institution': student.institution.name if student.institution else 'Engineering Institute',
            'headline': student.headline,
            'skills_count': student.skills.count(),
            'projects_count': student.projects.count(),
            'resumes_count': student.resumes.count(),
        }

    @classmethod
    def get_student_skills(cls, student: StudentProfile) -> List[Dict[str, Any]]:
        return [
            {
                'name': s.skill_name,
                'proficiency': s.get_proficiency_display(),
                'is_verified': s.is_verified
            }
            for s in student.skills.all()
        ]

    @classmethod
    def find_matching_jobs(
        cls,
        student: StudentProfile,
        keyword: str = '',
        location: str = '',
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Calculates skill affinity and eligibility for active jobs in NexGrad.
        """
        student_skills = {s.skill_name.lower() for s in student.skills.all()}
        student_branch = student.branch.upper()
        student_cgpa = float(student.cgpa or 0.0)

        qs = Job.objects.filter(is_active=True).select_related('company', 'recruiter')
        if keyword:
            qs = qs.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword) | Q(company__name__icontains=keyword))
        if location:
            qs = qs.filter(location__icontains=location)

        scored_jobs = []
        for job in qs[:40]:  # Evaluate candidate pool
            job_skills = {sk.name.lower() for sk in job.required_skills.all()}
            if not job_skills:
                # Extract simple keyword skills from title/description
                desc_lower = job.description.lower()
                for common in ['python', 'java', 'c++', 'javascript', 'react', 'sql', 'docker', 'aws', 'django']:
                    if common in desc_lower:
                        job_skills.add(common)

            # Match calculation
            common_skills = student_skills.intersection(job_skills)
            match_pct = 50
            if job_skills:
                match_pct = int((len(common_skills) / len(job_skills)) * 80) + 20
            match_pct = min(max(match_pct, 40), 98)

            # Eligibility checks
            branch_eligible = True
            if job.eligible_branches:
                eligible_list = [b.strip().upper() for b in job.eligible_branches.split(',')]
                if eligible_list and student_branch not in eligible_list and 'ALL' not in eligible_list:
                    branch_eligible = False

            cgpa_eligible = student_cgpa >= float(job.min_cgpa or 0.0)

            scored_jobs.append({
                'id': job.id,
                'title': job.title,
                'company': job.company.name,
                'location': job.location,
                'salary_range': job.salary_range,
                'workplace_type': job.get_workplace_type_display(),
                'match_percentage': match_pct,
                'branch_eligible': branch_eligible,
                'cgpa_eligible': cgpa_eligible,
                'is_fully_eligible': branch_eligible and cgpa_eligible,
                'matching_skills': list(common_skills)[:4],
                'missing_skills': list(job_skills - common_skills)[:4],
                'slug': job.slug,
            })

        # Sort by match score descending
        scored_jobs.sort(key=lambda x: (x['is_fully_eligible'], x['match_percentage']), reverse=True)
        top_jobs = scored_jobs[:limit]

        return {
            'count': len(top_jobs),
            'jobs': top_jobs,
            'summary': f"Found {len(top_jobs)} high-affinity engineering opportunities matching your profile."
        }

    @classmethod
    def get_jobs_by_ids(cls, student: StudentProfile, job_ids: List[int]) -> Dict[str, Any]:
        """
        Retrieves active jobs by exact IDs, maintaining original order and
        calculating student-specific compatibility.
        """
        if not job_ids:
            return {'count': 0, 'jobs': [], 'summary': "No active jobs found for the specified IDs."}

        student_skills = {s.skill_name.lower() for s in student.skills.all()}
        student_branch = student.branch.upper()
        student_cgpa = float(student.cgpa or 0.0)

        jobs_map = {
            j.id: j for j in Job.objects.filter(id__in=job_ids, is_active=True).select_related('company', 'recruiter')
        }

        ordered_jobs = []
        for j_id in job_ids:
            if j_id not in jobs_map:
                continue
            job = jobs_map[j_id]
            job_skills = {sk.name.lower() for sk in job.required_skills.all()}
            if not job_skills:
                desc_lower = job.description.lower()
                for common in ['python', 'java', 'c++', 'javascript', 'react', 'sql', 'docker', 'aws', 'django']:
                    if common in desc_lower:
                        job_skills.add(common)

            common_skills = student_skills.intersection(job_skills)
            match_pct = 50
            if job_skills:
                match_pct = int((len(common_skills) / len(job_skills)) * 80) + 20
            match_pct = min(max(match_pct, 40), 98)

            branch_eligible = True
            if job.eligible_branches:
                eligible_list = [b.strip().upper() for b in job.eligible_branches.split(',')]
                if eligible_list and student_branch not in eligible_list and 'ALL' not in eligible_list:
                    branch_eligible = False

            cgpa_eligible = student_cgpa >= float(job.min_cgpa or 0.0)

            ordered_jobs.append({
                'id': job.id,
                'title': job.title,
                'company': job.company.name,
                'location': job.location,
                'salary_range': job.salary_range,
                'workplace_type': job.get_workplace_type_display(),
                'match_percentage': match_pct,
                'branch_eligible': branch_eligible,
                'cgpa_eligible': cgpa_eligible,
                'is_fully_eligible': branch_eligible and cgpa_eligible,
                'matching_skills': list(common_skills)[:4],
                'missing_skills': list(job_skills - common_skills)[:4],
                'slug': job.slug,
            })

        return {
            'count': len(ordered_jobs),
            'jobs': ordered_jobs,
            'summary': f"Retrieved {len(ordered_jobs)} previously matched active opportunities."
        }

    @classmethod
    def get_job_detail_by_id(cls, student: StudentProfile, job_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieves detailed information and personalized eligibility check for a specific job.
        """
        job = Job.objects.filter(id=job_id, is_active=True).select_related('company', 'recruiter').first()
        if not job:
            return None

        student_skills = {s.skill_name.lower() for s in student.skills.all()}
        student_branch = student.branch.upper()
        student_cgpa = float(student.cgpa or 0.0)

        job_skills = {sk.name.lower() for sk in job.required_skills.all()}
        common_skills = student_skills.intersection(job_skills)
        match_pct = 50
        if job_skills:
            match_pct = int((len(common_skills) / len(job_skills)) * 80) + 20
        match_pct = min(max(match_pct, 40), 98)

        branch_eligible = True
        if job.eligible_branches:
            eligible_list = [b.strip().upper() for b in job.eligible_branches.split(',')]
            if eligible_list and student_branch not in eligible_list and 'ALL' not in eligible_list:
                branch_eligible = False

        cgpa_eligible = student_cgpa >= float(job.min_cgpa or 0.0)
        is_already_applied = Application.objects.filter(student=student, job=job).exists()

        return {
            'id': job.id,
            'title': job.title,
            'company': job.company.name,
            'location': job.location,
            'salary_range': job.salary_range,
            'workplace_type': job.get_workplace_type_display(),
            'description': job.description,
            'responsibilities': job.responsibilities,
            'requirements': job.requirements,
            'match_percentage': match_pct,
            'branch_eligible': branch_eligible,
            'cgpa_eligible': cgpa_eligible,
            'is_fully_eligible': branch_eligible and cgpa_eligible,
            'matching_skills': list(common_skills),
            'missing_skills': list(job_skills - common_skills),
            'eligible_branches': job.eligible_branches,
            'min_cgpa': float(job.min_cgpa or 0.0),
            'is_already_applied': is_already_applied,
            'slug': job.slug,
        }

    @classmethod
    def compare_jobs_by_ids(cls, student: StudentProfile, job_id_1: int, job_id_2: int) -> Optional[Dict[str, Any]]:
        """
        Side-by-side comparison of two active jobs for a student.
        """
        detail1 = cls.get_job_detail_by_id(student, job_id_1)
        detail2 = cls.get_job_detail_by_id(student, job_id_2)
        if not detail1 or not detail2:
            return None

        return {
            'job_1': detail1,
            'job_2': detail2,
            'summary': f"Comparison: {detail1['title']} ({detail1['company']}) vs. {detail2['title']} ({detail2['company']})"
        }

    @classmethod
    def prepare_application_draft(cls, student: StudentProfile, job_id: int) -> Dict[str, Any]:
        """
        Prepares an application draft and asks for student confirmation before submission.
        """
        job = Job.objects.filter(id=job_id, is_active=True).select_related('company').first()
        if not job:
            return {'error': 'The requested job vacancy is no longer active.'}

        already_applied = Application.objects.filter(student=student, job=job).first()
        if already_applied:
            return {
                'job_id': job.id,
                'job_title': job.title,
                'company': job.company.name,
                'is_already_applied': True,
                'status': already_applied.get_status_display(),
                'applied_at': already_applied.applied_at.strftime('%b %d, %Y'),
            }

        resume = student.resumes.filter(is_default=True).first() or student.resumes.first()
        return {
            'job_id': job.id,
            'job_title': job.title,
            'company': job.company.name,
            'salary_range': job.salary_range,
            'location': job.location,
            'resume_title': resume.title if resume else 'No verified resume uploaded',
            'resume_id': resume.id if resume else None,
            'is_already_applied': False,
            'summary': f"Please review and confirm your application for {job.title} at {job.company.name}."
        }

    @classmethod
    def confirm_and_submit_application(cls, student: StudentProfile, job_id: int, resume_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Explicitly submits an application after student confirmation.
        """
        job = Job.objects.filter(id=job_id, is_active=True).first()
        if not job:
            return {'success': False, 'error': 'The selected job vacancy is no longer active or does not exist.'}

        if Application.objects.filter(student=student, job=job).exists():
            return {'success': False, 'error': 'You have already submitted an application for this position.'}

        resume = None
        if resume_id:
            resume = student.resumes.filter(id=resume_id).first()
        if not resume:
            resume = student.resumes.filter(is_default=True).first() or student.resumes.first()

        app = Application.objects.create(
            student=student,
            job=job,
            resume=resume,
            status=Application.Status.APPLIED
        )

        return {
            'success': True,
            'application_id': app.id,
            'job_id': job.id,
            'job_title': job.title,
            'company': job.company.name,
            'applied_at': app.applied_at.strftime('%b %d, %Y'),
            'summary': f"Your application for {job.title} at {job.company.name} has been successfully submitted!"
        }

    @classmethod
    def find_matching_internships(
        cls,
        student: StudentProfile,
        keyword: str = '',
        location: str = '',
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Calculates skill affinity and eligibility for active internships in NexGrad.
        """
        student_skills = {s.skill_name.lower() for s in student.skills.all()}
        student_branch = student.branch.upper()

        qs = Internship.objects.filter(is_active=True).select_related('company')
        if keyword:
            qs = qs.filter(Q(title__icontains=keyword) | Q(description__icontains=keyword) | Q(company__name__icontains=keyword))
        if location:
            qs = qs.filter(location__icontains=location)

        scored_internships = []
        for intern in qs[:30]:
            req_skills = {sk.name.lower() for sk in intern.required_skills.all()}
            common_skills = student_skills.intersection(req_skills)
            match_pct = 60
            if req_skills:
                match_pct = int((len(common_skills) / len(req_skills)) * 75) + 25
            match_pct = min(max(match_pct, 45), 96)

            scored_internships.append({
                'id': intern.id,
                'title': intern.clean_title if hasattr(intern, 'clean_title') else intern.title,
                'company': intern.company.name,
                'location': intern.location,
                'duration': intern.duration,
                'stipend': intern.stipend,
                'match_percentage': match_pct,
                'matching_skills': list(common_skills)[:3],
                'missing_skills': list(req_skills - common_skills)[:3],
                'slug': intern.slug,
            })

        scored_internships.sort(key=lambda x: x['match_percentage'], reverse=True)
        top_interns = scored_internships[:limit]

        return {
            'count': len(top_interns),
            'internships': top_interns,
            'summary': f"Found {len(top_interns)} targeted internship programs aligned with your semester timeline."
        }

    @classmethod
    def analyse_skill_gaps(cls, student: StudentProfile, target_role: str) -> Dict[str, Any]:
        """
        Performs competitive market skill gap analysis against NexGrad job requisitions.
        """
        student_skills = {s.skill_name.lower(): s.proficiency for s in student.skills.all()}

        # Find jobs in platform matching the role
        jobs = Job.objects.filter(is_active=True).filter(
            Q(title__icontains=target_role) | Q(description__icontains=target_role)
        )[:15]

        market_skill_counts = {}
        for j in jobs:
            for sk in j.required_skills.all():
                name = sk.name.title()
                market_skill_counts[name] = market_skill_counts.get(name, 0) + 1

        # Default foundational skills if niche role has few explicit skill tags
        if not market_skill_counts:
            role_lower = target_role.lower()
            if 'data' in role_lower or 'ai' in role_lower or 'ml' in role_lower:
                market_skill_counts = {'Python': 10, 'SQL': 9, 'Pandas': 8, 'Machine Learning': 7, 'TensorFlow': 5, 'Docker': 4}
            elif 'devops' in role_lower or 'cloud' in role_lower or 'sre' in role_lower:
                market_skill_counts = {'Linux': 10, 'Docker': 9, 'Kubernetes': 9, 'AWS': 8, 'CI/CD': 7, 'Terraform': 6}
            elif 'frontend' in role_lower or 'ui' in role_lower:
                market_skill_counts = {'JavaScript': 10, 'React': 9, 'TypeScript': 8, 'CSS3': 8, 'Next.js': 6, 'Redux': 5}
            else:
                market_skill_counts = {'Python': 10, 'Data Structures': 9, 'Django': 8, 'SQL': 8, 'REST APIs': 7, 'Docker': 6}

        matched_skills = []
        missing_skills = []
        for skill_name, frequency in market_skill_counts.items():
            if skill_name.lower() in student_skills:
                matched_skills.append({
                    'name': skill_name,
                    'proficiency': student_skills[skill_name.lower()],
                    'market_demand': 'High' if frequency >= 5 else 'Medium'
                })
            else:
                missing_skills.append({
                    'name': skill_name,
                    'priority': 'Critical' if frequency >= 6 else 'Recommended',
                    'market_demand': 'High' if frequency >= 5 else 'Medium'
                })

        total_market = len(market_skill_counts)
        readiness_pct = int((len(matched_skills) / max(total_market, 1)) * 100)

        return {
            'target_role': target_role.title(),
            'readiness_score': readiness_pct,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'summary': f"You currently meet {readiness_pct}% of core technical criteria for {target_role.title()} positions."
        }

    @classmethod
    def create_learning_roadmap(
        cls,
        student: StudentProfile,
        target_role: str,
        duration_weeks: int = 12
    ) -> Dict[str, Any]:
        """
        Synthesizes a 4-phase, multi-week engineering roadmap customized to student's background.
        Saves to StudentLearningPlan.
        """
        role_clean = target_role.strip().title()

        # Build custom milestone phases
        phases = [
            {
                'phase_number': 1,
                'title': 'Core Foundations & Systems Thinking',
                'duration': f"Weeks 1-{max(duration_weeks // 4, 2)}",
                'description': f"Solidify fundamental programming paradigms, algorithms, and core design patterns for {role_clean}.",
                'tasks': [
                    {'key': 'f1', 'title': 'Master advanced data structures & algorithmic complexity (O(N) analysis)', 'completed': False},
                    {'key': 'f2', 'title': 'Implement clean modular coding standards with PEP-8 and linting', 'completed': False},
                    {'key': 'f3', 'title': 'Build a robust automated test suite using Pytest / unittest', 'completed': False},
                ],
                'project_milestone': 'Build a verified modular CLI utility with full unit test coverage.'
            },
            {
                'phase_number': 2,
                'title': 'Backend Systems & API Architecture',
                'duration': f"Weeks {duration_weeks // 4 + 1}-{duration_weeks // 2}",
                'description': 'Construct enterprise RESTful endpoints, relational schemas, indexing, and authentication flows.',
                'tasks': [
                    {'key': 'a1', 'title': 'Design normalized relational models with foreign keys & indexing in PostgreSQL', 'completed': False},
                    {'key': 'a2', 'title': 'Implement role-based authorization (RBAC) and JWT authentication', 'completed': False},
                    {'key': 'a3', 'title': 'Configure database connection pooling and query optimization', 'completed': False},
                ],
                'project_milestone': 'Develop a production-grade multi-tenant REST API with JWT authorization.'
            },
            {
                'phase_number': 3,
                'title': 'Cloud Infrastructure, Containers & DevOps',
                'duration': f"Weeks {duration_weeks // 2 + 1}-{(duration_weeks * 3) // 4}",
                'description': 'Containerization, continuous integration/continuous deployment pipelines, and observability.',
                'tasks': [
                    {'key': 'd1', 'title': 'Dockerize the application stack with multi-stage production Dockerfiles', 'completed': False},
                    {'key': 'd2', 'title': 'Setup GitHub Actions CI workflow for linting, security scans, and tests', 'completed': False},
                    {'key': 'd3', 'title': 'Integrate structured JSON logging and health check endpoints', 'completed': False},
                ],
                'project_milestone': 'Deploy containerized web service to cloud platform with automated CI/CD pipeline.'
            },
            {
                'phase_number': 4,
                'title': 'Advanced Scale & Capstone Defense',
                'duration': f"Weeks {(duration_weeks * 3) // 4 + 1}-{duration_weeks}",
                'description': f"Finalize portfolio capstone demonstrating high-throughput resilience expected in {role_clean} hiring.",
                'tasks': [
                    {'key': 'c1', 'title': 'Implement Redis caching layer for high-frequency queries', 'completed': False},
                    {'key': 'c2', 'title': 'Draft comprehensive architectural documentation and system diagrams', 'completed': False},
                    {'key': 'c3', 'title': 'Conduct simulated technical project walkthrough and interview defense', 'completed': False},
                ],
                'project_milestone': f"Full-stack {role_clean} Capstone project hosted live with GitHub repo and architecture docs."
            }
        ]

        # Deactivate old plans for same role
        StudentLearningPlan.objects.filter(student=student, target_role__iexact=role_clean).update(is_active=False)

        plan = StudentLearningPlan.objects.create(
            student=student,
            title=f"{role_clean} Accelerated Mastery Path",
            target_role=role_clean,
            duration_weeks=duration_weeks,
            phases=phases,
            is_active=True
        )

        for p_idx, phase in enumerate(phases):
            for t in phase['tasks']:
                LearningPlanProgress.objects.create(
                    plan=plan,
                    phase_index=p_idx,
                    task_key=t['key'],
                    task_title=t['title'],
                    is_completed=False
                )

        return {
            'plan_id': plan.id,
            'title': plan.title,
            'target_role': plan.target_role,
            'duration_weeks': plan.duration_weeks,
            'phases': phases,
            'summary': f"Created tailored {duration_weeks}-week roadmap for {role_clean} with 4 actionable engineering milestones."
        }

    @classmethod
    def conduct_mock_interview(
        cls,
        student: StudentProfile,
        target_role: str,
        interview_type: str = 'TECHNICAL',
        student_response: Optional[str] = None,
        session_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Conducts an interactive, turn-by-turn mock interview.
        Evaluates answers against technical rubrics and provides the next question.
        """
        session = None
        if session_id:
            try:
                session = InterviewSession.objects.get(id=session_id, student=student)
            except InterviewSession.DoesNotExist:
                session = None

        if not session:
            # Create a new session
            session = InterviewSession.objects.create(
                student=student,
                target_role=target_role.title(),
                interview_type=interview_type,
                status=InterviewSession.Status.IN_PROGRESS
            )

        # Question bank per role & type
        questions_pool = [
            f"Explain how you would design a rate-limiter for a public API in a {target_role} role. What algorithms (token bucket, sliding window) would you consider and how would you store state across distributed instances?",
            f"Walk me through a technically challenging bug you encountered in one of your recent projects. How did you isolate the root cause, what tools did you use to debug, and how did you verify the fix?",
            f"In a relational database like PostgreSQL, when would you add a composite B-Tree index versus separate single-column indexes, and what trade-offs does indexing introduce on write operations?",
            f"Explain how you handle state management, error boundaries, and race conditions when multiple asynchronous network requests are fired simultaneously.",
        ]

        # Evaluate previous question if student answered
        last_q = session.questions.filter(student_response='').order_by('order').first()
        feedback_data = None

        if student_response and last_q:
            last_q.student_response = student_response.strip()
            # Grade answer based on length, depth, and clarity
            words = len(last_q.student_response.split())
            score = 6
            strengths = []
            improvements = []

            if words > 70:
                score += 2
                strengths.append("Thorough structural explanation with good contextual detail.")
            else:
                improvements.append("Response is somewhat brief; elaborate on architectural trade-offs.")

            resp_lower = last_q.student_response.lower()
            if any(k in resp_lower for k in ['redis', 'trade-off', 'latency', 'index', 'complexity', 'lock', 'scale', 'cache']):
                score += 1
                strengths.append("Demonstrated solid grasp of production systems and latency considerations.")
            else:
                improvements.append("Cite specific enterprise technologies (e.g. Redis, message queues, B-Trees) to show production readiness.")

            score = min(max(score, 4), 10)
            last_q.score = score
            last_q.feedback = f"Score: {score}/10. Strengths: {'; '.join(strengths)}. To refine: {'; '.join(improvements)}"
            last_q.model_answer = "A senior engineering candidate answers this by first stating the design constraints (throughput, precision), comparing Token Bucket vs Sliding Window Counter, and choosing Redis with Lua scripts to prevent race conditions atomically."
            last_q.save()

            feedback_data = {
                'question': last_q.question_text,
                'score': score,
                'strengths': strengths,
                'improvements': improvements,
                'feedback': last_q.feedback,
                'model_answer': last_q.model_answer
            }
        elif not student_response and last_q:
            last_q.student_response = "[Skipped by candidate]"
            last_q.feedback = "Question skipped without submission."
            last_q.score = 5
            last_q.save()

        # Check how many questions completed
        answered_count = session.questions.exclude(student_response='').count()

        if answered_count >= 3:
            # Complete the session
            session.status = InterviewSession.Status.COMPLETED
            session.completed_at = timezone.now()
            avg_score = round(sum(q.score for q in session.questions.all()) / max(session.questions.count(), 1), 1)
            session.overall_feedback = f"Mock Interview Complete! Overall Performance Rating: {avg_score}/10. Candidate exhibited structured reasoning and practical technical problem solving."
            session.rubric_scores = {'overall_score': avg_score, 'questions_completed': answered_count}
            session.save()

            return {
                'session_id': session.id,
                'status': 'COMPLETED',
                'is_finished': True,
                'overall_score': avg_score,
                'summary': session.overall_feedback,
                'last_feedback': feedback_data
            }

        # Next question
        next_order = answered_count + 1
        new_q = session.questions.filter(order=next_order).first()
        if not new_q:
            q_idx = min(next_order - 1, len(questions_pool) - 1)
            next_q_text = questions_pool[q_idx]
            new_q = InterviewQuestion.objects.create(
                session=session,
                order=next_order,
                question_text=next_q_text
            )

        return {
            'session_id': session.id,
            'status': 'IN_PROGRESS',
            'is_finished': False,
            'question_number': next_order,
            'total_questions': 3,
            'question_text': new_q.question_text,
            'last_feedback': feedback_data,
            'summary': f"Question {next_order} of 3 for {session.target_role} ({session.get_interview_type_display()})."
        }

    @classmethod
    def analyse_resume(
        cls,
        student: StudentProfile,
        resume_id: Optional[int] = None,
        target_role: str = 'Software Engineer'
    ) -> Dict[str, Any]:
        """
        Conducts deep resume and profile analysis, identifying missing metrics and role keywords.
        """
        resume = None
        if resume_id:
            try:
                resume = student.resumes.get(id=resume_id)
            except Resume.DoesNotExist:
                resume = None
        if not resume:
            resume = student.resumes.filter(is_default=True).first() or student.resumes.first()

        strengths = [
            f"Strong academic foundation ({student.degree} in {student.get_branch_display()} with {student.cgpa} CGPA).",
            f"Documented hands-on technical skills ({student.skills.count()} skills registered).",
        ]
        if student.projects.exists():
            strengths.append(f"Demonstrated project portfolio ({student.projects.count()} open projects linked).")

        gaps = [
            "Project bullet points lack quantifiable impact metrics (e.g. latency reduction %, user volume, test coverage %).",
            f"Keyword density for '{target_role}' needs enrichment with industry-standard tooling.",
        ]
        if not student.github_url:
            gaps.append("Missing public GitHub repository link on main profile.")

        improvements = [
            "Rewrite project bullets using the Google XYZ formula: 'Accomplished [X] as measured by [Y], by doing [Z]'.",
            f"Group technical skills into clear categories: Languages, Frameworks, Databases, and Cloud/DevOps.",
            f"Include a focused 2-line Professional Summary tailored specifically to {target_role} roles.",
        ]

        keywords = ['Docker', 'CI/CD Pipelines', 'REST APIs', 'PostgreSQL', 'System Architecture', 'Automated Testing']

        analysis = ResumeAnalysis.objects.create(
            student=student,
            resume=resume,
            target_role=target_role.title(),
            strengths=strengths,
            gaps=gaps,
            improvements=improvements,
            suggested_summary=f"Proactive {student.get_branch_display()} student with hands-on proficiency in {', '.join([s.skill_name for s in student.skills.all()[:3]]) or 'modern software engineering'}. Experienced in building full-stack applications with clean architecture and automated tests, seeking to contribute to scalable engineering systems as a {target_role.title()}.",
            keyword_recommendations=keywords
        )

        return {
            'analysis_id': analysis.id,
            'target_role': analysis.target_role,
            'strengths': strengths,
            'gaps': gaps,
            'improvements': improvements,
            'suggested_summary': analysis.suggested_summary,
            'keyword_recommendations': keywords,
            'summary': f"Resume audit for {target_role.title()} completed with actionable bullet-point recommendations."
        }

    @classmethod
    def get_application_status(cls, student: StudentProfile) -> Dict[str, Any]:
        apps = student.applications.select_related('job__company', 'internship__company').order_by('-applied_at')[:8]
        items = []
        for a in apps:
            items.append({
                'role': a.role_title,
                'company': a.company_name,
                'status': a.get_status_display(),
                'status_code': a.status,
                'applied_at': a.applied_at.strftime('%b %d, %Y'),
            })
        return {
            'total_applications': student.applications.count(),
            'recent_applications': items,
            'summary': f"You have {student.applications.count()} total applications tracked in NexGrad."
        }

    @classmethod
    def get_assessment_results(cls, student: StudentProfile) -> Dict[str, Any]:
        attempts = student.assessment_attempts.select_related('assessment').order_by('-started_at')[:6]
        items = []
        for att in attempts:
            items.append({
                'title': att.assessment.title,
                'category': att.assessment.category,
                'score': att.score,
                'is_passed': att.is_passed,
                'passing_marks': att.assessment.passing_marks,
                'date': att.started_at.strftime('%b %d, %Y'),
            })
        return {
            'total_assessments': student.assessment_attempts.count(),
            'assessments': items,
            'summary': f"Completed {student.assessment_attempts.count()} technical assessments on NexGrad."
        }

