"""
Nexgrad Database Seeder
Populates realistic demonstration data for academic evaluation & viva demonstration.
Run via: python seed_data.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nexgrad.settings')
django.setup()

from django.utils.text import slugify
from accounts.models import CustomUser
from institutions.models import Institution, Department
from recruiters.models import Company, RecruiterProfile
from students.models import StudentProfile, Project, StudentSkill
from jobs.models import Skill, Job, Internship
from assessments.models import Assessment
from career_intelligence.models import CareerRoadmap, RoadmapMilestone
from applications.models import Application, ApplicationStatusHistory
from notifications.models import Notification
from challenges.models import Challenge, ChallengeAssignment, ChallengeSubmission, ChallengeEvent
from datetime import timedelta
from django.utils import timezone

def seed():
    print("Seeding Nexgrad Database...")

    # 1. Platform Superuser / Administrator
    if not CustomUser.objects.filter(username='admin').exists():
        admin_user = CustomUser.objects.create_superuser(
            username='admin',
            email='admin@nexgrad.edu',
            password='adminpassword123',
            first_name='System',
            last_name='Administrator',
            role=CustomUser.Role.ADMIN,
            is_verified=True
        )
        print("Created Superuser: admin / adminpassword123")
    else:
        admin_user = CustomUser.objects.get(username='admin')

    # 2. Institution & Department
    inst, _ = Institution.objects.get_or_create(
        name='National Institute of Technology & Engineering',
        defaults={
            'slug': 'nite-university',
            'code': 'NITE-01',
            'website': 'https://nite.edu.in',
            'location': 'Bengaluru, Karnataka',
            'is_verified': True
        }
    )
    dept_cse, _ = Department.objects.get_or_create(
        institution=inst,
        name='Computer Science & Engineering',
        defaults={'code': 'CSE'}
    )
    dept_ece, _ = Department.objects.get_or_create(
        institution=inst,
        name='Electronics & Communication',
        defaults={'code': 'ECE'}
    )
    print(f"Created Institution: {inst.name}")

    # 3. Technical Skills
    skills_data = [
        ('Python', 'BACKEND'),
        ('Django', 'BACKEND'),
        ('PostgreSQL', 'DATABASE'),
        ('Docker', 'CLOUD'),
        ('AWS Cloud', 'CLOUD'),
        ('Data Structures & Algorithms', 'SYSTEMS'),
        ('React.js', 'FRONTEND'),
        ('PyTorch & Deep Learning', 'AI_ML'),
        ('System Architecture', 'BACKEND'),
    ]
    created_skills = {}
    for name, cat in skills_data:
        s, _ = Skill.objects.get_or_create(name=name, defaults={'category': cat, 'slug': slugify(name)})
        created_skills[name] = s
    print(f"Created {len(created_skills)} Technical Skills.")

    # 4. Companies & Recruiters
    comp1, _ = Company.objects.get_or_create(
        name='Arcturus Cloud Technologies',
        defaults={
            'slug': 'arcturus-cloud-technologies',
            'industry': 'Cloud & Enterprise Infrastructure',
            'website': 'https://arcturus.example.com',
            'description': 'Building next-generation distributed systems and high-throughput data processing engines.',
            'headquarters': 'Bengaluru, India',
            'company_size': '250-500 Employees',
            'is_verified': True
        }
    )

    comp2, _ = Company.objects.get_or_create(
        name='Novus Robotics & Embedded AI',
        defaults={
            'slug': 'novus-robotics',
            'industry': 'Robotics, IoT & Edge Computing',
            'website': 'https://novusrobotics.example.com',
            'description': 'Autonomous aerial and ground robotic hardware and edge machine vision platforms.',
            'headquarters': 'Hyderabad, India',
            'company_size': '50-100 Employees',
            'is_verified': True
        }
    )

    recruiter_user, created = CustomUser.objects.get_or_create(
        username='recruiter_sarah',
        defaults={
            'email': 'sarah.jenkins@arcturus.com',
            'first_name': 'Sarah',
            'last_name': 'Jenkins',
            'role': CustomUser.Role.RECRUITER,
            'is_verified': True
        }
    )
    if created:
        recruiter_user.set_password('recruiter123')
        recruiter_user.save()

    recruiter_prof, _ = RecruiterProfile.objects.get_or_create(
        user=recruiter_user,
        defaults={
            'company': comp1,
            'designation': 'Head of Engineering Talent',
            'is_verified': True
        }
    )
    print(f"Created Recruiter: {recruiter_user.username}")

    # 5. Engineering Student
    student_user, created = CustomUser.objects.get_or_create(
        username='student_arjun',
        defaults={
            'email': 'arjun.mehta@nite.edu.in',
            'first_name': 'Arjun',
            'last_name': 'Mehta',
            'role': CustomUser.Role.STUDENT,
            'is_verified': True
        }
    )
    if created:
        student_user.set_password('student123')
        student_user.save()

    student_prof, _ = StudentProfile.objects.get_or_create(
        user=student_user,
        defaults={
            'institution': inst,
            'department': dept_cse,
            'branch': 'CSE',
            'degree': 'B.Tech',
            'graduation_year': 2026,
            'cgpa': 8.85,
            'headline': 'Backend & Cloud Systems Engineer | Open Source Contributor',
            'bio': 'Passionate about distributed backend architecture, database optimization, and high-performance Python microservices.',
            'location': 'Bengaluru, India',
            'github_url': 'https://github.com/arjunmehta-dev',
            'portfolio_url': 'https://arjunmehta.tech',
        }
    )

    # Student Skills & Projects
    for s_name in ['Python', 'Django', 'PostgreSQL', 'Docker']:
        StudentSkill.objects.get_or_create(
            student=student_prof,
            skill_name=s_name,
            defaults={'proficiency': 'ADVANCED', 'is_verified': True}
        )

    Project.objects.get_or_create(
        student=student_prof,
        title='Distributed Task Queue Engine in Python',
        defaults={
            'description': 'A lightweight asynchronous event worker with priority scheduling and SQLite/Redis backing.',
            'technologies': 'Python, Concurrency, Sockets, SQLite',
            'repo_url': 'https://github.com/arjunmehta-dev/task-queue',
            'contribution_summary': 'Engineered round-robin consumer pool and retry backoff mechanics.'
        }
    )
    print(f"Created Student Profile: {student_user.username}")

    # 6. Engineering Jobs & Internships
    job1, _ = Job.objects.get_or_create(
        title='Backend Software Engineer (Python/Django)',
        company=comp1,
        defaults={
            'recruiter': recruiter_prof,
            'job_type': 'FULL_TIME',
            'workplace_type': 'HYBRID',
            'location': 'Bengaluru, India',
            'salary_range': '₹12,00,000 - ₹18,00,000 P.A.',
            'description': 'We are seeking an ambitious software engineer to build scalable backend services, design resilient relational databases, and collaborate on distributed microservices.',
            'responsibilities': 'Design clean REST endpoints, write optimized ORM queries, implement automated unit test suites.',
            'requirements': 'Strong grasp of Python fundamentals, relational schema design, Git version control, and web protocols.',
            'eligible_branches': 'CSE, ECE, IT',
            'min_cgpa': 7.50,
            'openings': 4,
            'is_active': True,
        }
    )
    job1.required_skills.set([created_skills['Python'], created_skills['Django'], created_skills['PostgreSQL']])

    job2, _ = Job.objects.get_or_create(
        title='Cloud & DevOps Trainee Engineer',
        company=comp1,
        defaults={
            'recruiter': recruiter_prof,
            'job_type': 'GRADUATE',
            'workplace_type': 'REMOTE',
            'location': 'Remote / Bengaluru',
            'salary_range': '₹9,00,000 - ₹13,00,000 P.A.',
            'description': 'Join our cloud infrastructure team automating continuous integration, provisioning cloud nodes, and monitoring service reliability.',
            'eligible_branches': 'CSE, ECE, EE, IT',
            'min_cgpa': 7.00,
            'openings': 3,
            'is_active': True,
        }
    )
    job2.required_skills.set([created_skills['Docker'], created_skills['AWS Cloud'], created_skills['Python']])

    job3, _ = Job.objects.get_or_create(
        title='Embedded Systems & Edge AI Engineer',
        company=comp2,
        defaults={
            'recruiter': recruiter_prof,
            'job_type': 'FULL_TIME',
            'workplace_type': 'ON_SITE',
            'location': 'Hyderabad, India',
            'salary_range': '₹10,00,000 - ₹16,00,000 P.A.',
            'description': 'Deploy computer vision and machine learning models on constrained edge hardware for real-time robotic navigation.',
            'eligible_branches': 'CSE, ECE, EE',
            'min_cgpa': 8.00,
            'openings': 2,
            'is_active': True,
        }
    )
    job3.required_skills.set([created_skills['PyTorch & Deep Learning'], created_skills['Data Structures & Algorithms']])

    intern1, _ = Internship.objects.get_or_create(
        title='Software Engineering Summer Intern',
        company=comp1,
        defaults={
            'recruiter': recruiter_prof,
            'duration': '6 Months',
            'stipend': '₹45,000 / Month',
            'location': 'Bengaluru (Hybrid)',
            'description': 'Work alongside senior software architects building real production features on our core cloud platform.',
            'eligible_branches': 'CSE, ECE, IT',
            'is_active': True,
        }
    )
    intern1.required_skills.set([created_skills['Python'], created_skills['Django']])
    print("Created 3 Jobs and 1 Internship.")

    # 7. Technical Assessments
    assm1, _ = Assessment.objects.get_or_create(
        title='Python Core & Backend Systems Evaluation',
        defaults={
            'category': 'Python & Backend Systems',
            'difficulty': 'INTERMEDIATE',
            'duration_minutes': 45,
            'total_marks': 100,
            'passing_marks': 60,
            'description': 'Evaluates algorithmic proficiency, database query optimization, and REST API conventions.',
            'is_active': True
        }
    )

    assm2, _ = Assessment.objects.get_or_create(
        title='Data Structures & Algorithmic Problem Solving',
        defaults={
            'category': 'Core Computer Science',
            'difficulty': 'ADVANCED',
            'duration_minutes': 60,
            'total_marks': 100,
            'passing_marks': 65,
            'description': 'Tests complex graph traversals, dynamic programming, and space-time complexity analysis.',
            'is_active': True
        }
    )
    print("Created 2 Technical Assessments.")

    # 8. Career Roadmaps
    rm1, _ = CareerRoadmap.objects.get_or_create(
        title='Full Stack Systems Engineer',
        defaults={
            'slug': 'full-stack-systems-engineer',
            'target_role': 'Full Stack Systems Engineer',
            'summary': 'Comprehensive path mastering end-to-end web architecture, relational databases, and cloud deployment.',
            'is_active': True
        }
    )
    RoadmapMilestone.objects.get_or_create(
        roadmap=rm1,
        order=1,
        defaults={
            'level': 'FOUNDATIONAL',
            'title': 'Foundational Python & Relational Modeling',
            'description': 'Object-oriented programming, schema design, and query optimization.',
            'recommended_skills': 'Python, SQL, PostgreSQL'
        }
    )
    RoadmapMilestone.objects.get_or_create(
        roadmap=rm1,
        order=2,
        defaults={
            'level': 'INTERMEDIATE',
            'title': 'Web Architecture & API Engineering',
            'description': 'Model-View-Template design, token authentication, and asynchronous tasks.',
            'recommended_skills': 'Django, REST APIs, Docker'
        }
    )
    print("Created Career Roadmaps.")

    # 9. Private Recruiter Challenges & Assignments (CareerForge Feature)
    sarah_recruiter = RecruiterProfile.objects.filter(user__username='recruiter_sarah').first()
    student_arjun = StudentProfile.objects.filter(user__username='student_arjun').first()
    first_job = Job.objects.filter(recruiter=sarah_recruiter).first()

    if sarah_recruiter and student_arjun:
        demo_challenge, _ = Challenge.objects.get_or_create(
            title='Django REST API & Celery Task Pipeline',
            defaults={
                'recruiter': sarah_recruiter,
                'job': first_job,
                'slug': 'django-rest-api-celery-pipeline',
                'challenge_type': Challenge.ChallengeType.CODING,
                'difficulty': Challenge.Difficulty.INTERMEDIATE,
                'description': 'Develop a secure, high-throughput REST API with asynchronous background processing and Redis caching.',
                'problem_statement': (
                    'Build an asynchronous data processing service using Django REST Framework.\n'
                    'Requirements:\n'
                    '1. Implement JWT/Token authentication with role permissions.\n'
                    '2. Expose CRUD endpoints for batch data ingestion.\n'
                    '3. Offload compute-heavy metrics calculation to asynchronous Celery tasks with Redis.\n'
                    '4. Implement Redis rate limiting (max 60 requests/minute per API key).\n'
                    '5. Write comprehensive pytest unit tests achieving >= 80% code coverage.'
                ),
                'instructions': 'Submit your GitHub repository link and an architecture summary explaining your queue design and caching strategy.',
                'technical_requirements': 'Python 3.12+, Django 5.x, Django REST Framework, Celery, Redis, PostgreSQL/SQLite.',
                'required_skills': 'Python, Django, REST APIs, Celery, Redis, pytest',
                'maximum_marks': 100,
                'deadline': timezone.now() + timedelta(days=7),
                'time_limit_minutes': 240,
                'allowed_submission_formats': 'Source Code, ZIP, GitHub Repository, Live Demo URL',
                'status': Challenge.Status.PUBLISHED
            }
        )

        # Get or create student application for the job
        if first_job:
            app, _ = Application.objects.get_or_create(
                student=student_arjun,
                job=first_job,
                defaults={
                    'status': Application.Status.ASSESSMENT,
                    'cover_letter': 'I am excited to apply my full-stack Python skills to this opportunity.'
                }
            )
        else:
            app = None

        # Create private challenge assignment
        assignment, created_assign = ChallengeAssignment.objects.get_or_create(
            challenge=demo_challenge,
            student=student_arjun,
            defaults={
                'application': app,
                'assigned_by': sarah_recruiter.user,
                'deadline': timezone.now() + timedelta(days=7),
                'status': ChallengeAssignment.Status.IN_PROGRESS,
                'started_at': timezone.now() - timedelta(hours=4)
            }
        )

        # Create notification for student
        Notification.objects.get_or_create(
            recipient=student_arjun.user,
            title=f"Technical Challenge Assigned: {demo_challenge.title}",
            defaults={
                'message': (
                    f"Congratulations! You have been shortlisted for the {first_job.title if first_job else 'Engineering'} position at {sarah_recruiter.company.name if sarah_recruiter.company else 'NexCloud'}. "
                    f"The recruiter has assigned you a private technical challenge as the next stage of the recruitment process. "
                    f"Please review the instructions and submit your solution before the specified deadline."
                ),
                'notification_type': 'ASSESSMENT',
                'is_read': False
            }
        )
        print("Created Demo Private Challenge and Candidate Assignment.")

    print("Database seeding completed successfully!")

if __name__ == '__main__':
    seed()

