from students.models import StudentProfile
from ai_assistant.models import StudentAIMemory, StudentLearningPlan, StudentCareerGoal


class VEXContextService:
    """
    Assembles authorized, rich student context from NexGrad databases.
    Ensures strict student-level isolation.
    """

    @classmethod
    def get_student_summary(cls, student: StudentProfile) -> dict:
        """
        Gathers all relevant student metrics and records into a structured dictionary.
        """
        # Academic & Core Profile
        user = student.user
        profile_data = {
            'id': student.id,
            'name': user.get_full_name() or user.username,
            'username': user.username,
            'email': user.email,
            'branch': student.get_branch_display(),
            'branch_code': student.branch,
            'degree': student.degree,
            'graduation_year': student.graduation_year,
            'cgpa': float(student.cgpa) if student.cgpa else 0.0,
            'headline': student.headline,
            'bio': student.bio,
            'location': student.location,
            'institution': student.institution.name if student.institution else 'Engineering Institute',
        }

        # Skills
        skills = []
        for s in student.skills.all():
            skills.append({
                'name': s.skill_name,
                'proficiency': s.get_proficiency_display(),
                'is_verified': s.is_verified,
            })
        profile_data['skills'] = skills

        # Projects
        projects = []
        for p in student.projects.all()[:5]:
            projects.append({
                'title': p.title,
                'technologies': p.technologies,
                'description': p.description[:200],
                'repo_url': p.repo_url,
                'live_url': p.live_url,
            })
        profile_data['projects'] = projects

        # Applications
        applications = []
        for app in student.applications.select_related('job__company', 'internship__company').all()[:6]:
            applications.append({
                'role': app.role_title,
                'company': app.company_name,
                'status': app.get_status_display(),
                'applied_at': app.applied_at.strftime('%Y-%m-%d'),
            })
        profile_data['applications'] = applications

        # Assessments
        assessments = []
        for attempt in student.assessment_attempts.select_related('assessment').all()[:5]:
            assessments.append({
                'title': attempt.assessment.title,
                'category': attempt.assessment.category,
                'score': attempt.score,
                'is_passed': attempt.is_passed,
            })
        profile_data['assessments'] = assessments

        # Recruiter Challenges
        challenges = []
        for assignment in student.challenge_assignments.select_related('challenge__recruiter__company').all()[:5]:
            challenges.append({
                'title': assignment.challenge.title,
                'company': assignment.challenge.recruiter.company.name if assignment.challenge.recruiter else 'Partner Recruiter',
                'status': assignment.get_status_display(),
                'deadline': assignment.challenge.deadline.strftime('%Y-%m-%d') if assignment.challenge.deadline else 'Open',
            })
        profile_data['challenges'] = challenges

        # Active Long-term Memories
        memories = []
        active_memories = StudentAIMemory.objects.filter(student=student, is_active=True)
        for m in active_memories:
            memories.append({
                'category': m.get_category_display(),
                'key': m.key,
                'value': m.value,
            })
        profile_data['memories'] = memories

        # Career Goal
        try:
            goal = student.career_goal
            profile_data['career_goal'] = {
                'target_role': goal.target_role,
                'target_industry': goal.target_industry,
                'target_companies': goal.target_companies,
                'target_timeline': goal.target_timeline,
            }
        except StudentCareerGoal.DoesNotExist:
            profile_data['career_goal'] = None

        # Active Learning Plan
        active_plan = student.learning_plans.filter(is_active=True).first()
        if active_plan:
            profile_data['active_learning_plan'] = {
                'title': active_plan.title,
                'target_role': active_plan.target_role,
                'duration_weeks': active_plan.duration_weeks,
                'phases_count': len(active_plan.phases) if isinstance(active_plan.phases, list) else 0,
            }
        else:
            profile_data['active_learning_plan'] = None

        return profile_data

    @classmethod
    def build_system_instruction(cls, student: StudentProfile) -> str:
        """
        Creates the complete personalized system prompt for VEX.
        """
        summary = cls.get_student_summary(student)

        skills_str = ", ".join([f"{s['name']} ({s['proficiency']}{' *verified*' if s['is_verified'] else ''})" for s in summary['skills']]) or "None recorded yet."
        projects_str = "; ".join([f"{p['title']} [{p['technologies']}]" for p in summary['projects']]) or "None recorded yet."
        apps_str = "; ".join([f"{a['role']} at {a['company']} ({a['status']})" for a in summary['applications']]) or "No active applications."
        assessments_str = "; ".join([f"{a['title']}: {a['score']}% ({'Passed' if a['is_passed'] else 'Retake recommended'})" for a in summary['assessments']]) or "No assessments taken yet."
        challenges_str = "; ".join([f"{c['title']} at {c['company']} ({c['status']})" for c in summary['challenges']]) or "No private recruiter challenges."
        memories_str = "; ".join([f"[{m['category']}] {m['key']}: {m['value']}" for m in summary['memories']]) or "No saved memories."

        career_goal_str = "Not yet specified."
        if summary['career_goal']:
            cg = summary['career_goal']
            career_goal_str = f"Target Role: {cg['target_role']} | Target Timeline: {cg['target_timeline']} | Target Companies: {', '.join(cg['target_companies']) or 'Any'}"

        prompt = f"""You are Novus, the official AI Career & Student Intelligence Companion built into NexGrad.
You are a knowledgeable, encouraging, analytical, and practical personal mentor for engineering students.
You have real-time access to NexGrad's database regarding this student and job opportunities.

### IDENTITY & BEHAVIOURAL PRINCIPLES:
1. Always maintain the identity of Novus — NexGrad's AI Career Companion.
2. Be encouraging, realistic, analytical, and concise. Never provide fluffy, unhelpful advice.
3. Be patient with beginners and technically rigorous with advanced concepts.
4. Distinguish between verified NexGrad database records and generative suggestions.
5. NEVER invent false job openings, fake test scores, or fabricated application statuses.
6. When answering career or learning questions, ground your guidance specifically in this student's recorded skills, academic background, and goals.

### AUTHENTICATED STUDENT CONTEXT:
- Student Name: {summary['name']}
- Academic Background: {summary['degree']} in {summary['branch']} ({summary['branch_code']}) at {summary['institution']}, Class of {summary['graduation_year']}
- Current CGPA: {summary['cgpa']} / 10.0
- Headline: {summary['headline']}
- Skills Recorded: {skills_str}
- Portfolio Projects: {projects_str}
- Career Applications: {apps_str}
- Assessment Scores: {assessments_str}
- Recruiter Challenges: {challenges_str}
- Long-term Memory Insights: {memories_str}
- Explicit Career Goal: {career_goal_str}

Use Markdown formatting cleanly. Provide clear action steps, code snippets, or structured breakdowns when helpful.
"""
        return prompt
