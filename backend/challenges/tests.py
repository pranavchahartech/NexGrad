from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from accounts.models import CustomUser
from recruiters.models import Company, RecruiterProfile
from students.models import StudentProfile
from jobs.models import Job
from applications.models import Application
from challenges.models import (
    Challenge, ChallengeAssignment, ChallengeSubmission,
    ChallengeEvaluation, ChallengeEvent
)

class RecruiterPrivateChallengeSystemTests(TestCase):
    """
    Automated test suite fulfilling Section 12 requirements:
    Recruiter-Assigned Private Challenges & Selected Candidate Assessment System.
    """

    def setUp(self):
        # 1. Setup Company A and Recruiter A
        self.company_a = Company.objects.create(name='NexCloud Systems', slug='nexcloud-systems')
        self.recruiter_user_a = CustomUser.objects.create_user(
            username='recruiter_alice',
            email='alice@nexcloud.io',
            password='password123',
            role=CustomUser.Role.RECRUITER
        )
        self.recruiter_profile_a = RecruiterProfile.objects.create(
            user=self.recruiter_user_a,
            company=self.company_a,
            designation='Lead Tech Recruiter'
        )

        # 2. Setup Company B and Recruiter B
        self.company_b = Company.objects.create(name='DataCore Labs', slug='datacore-labs')
        self.recruiter_user_b = CustomUser.objects.create_user(
            username='recruiter_bob',
            email='bob@datacore.io',
            password='password123',
            role=CustomUser.Role.RECRUITER
        )
        self.recruiter_profile_b = RecruiterProfile.objects.create(
            user=self.recruiter_user_b,
            company=self.company_b,
            designation='Talent Lead'
        )

        # 3. Setup Students (Arjun & Bhavna)
        self.student_user_1 = CustomUser.objects.create_user(
            username='student_arjun',
            email='arjun@test.edu',
            password='password123',
            role=CustomUser.Role.STUDENT
        )
        self.student_profile_1 = StudentProfile.objects.create(user=self.student_user_1, branch='CSE')

        self.student_user_2 = CustomUser.objects.create_user(
            username='student_bhavna',
            email='bhavna@test.edu',
            password='password123',
            role=CustomUser.Role.STUDENT
        )
        self.student_profile_2 = StudentProfile.objects.create(user=self.student_user_2, branch='ECE')

        # 4. Setup Vacancy & Application
        self.job = Job.objects.create(
            recruiter=self.recruiter_profile_a,
            company=self.company_a,
            title='Backend Python Engineer',
            slug='nexcloud-backend-python',
            description='Build REST APIs using Django'
        )
        self.application = Application.objects.create(
            student=self.student_profile_1,
            job=self.job,
            status=Application.Status.SHORTLISTED
        )

        # 5. Setup Private Challenge for Company A
        self.deadline = timezone.now() + timedelta(days=5)
        self.challenge = Challenge.objects.create(
            recruiter=self.recruiter_profile_a,
            job=self.job,
            title='Django REST API Challenge',
            challenge_type=Challenge.ChallengeType.CODING,
            description='Build an asynchronous task queue API',
            problem_statement='Implement rate limiting and token authentication.',
            maximum_marks=100,
            deadline=self.deadline,
            status=Challenge.Status.PUBLISHED
        )

        self.client = Client()

    def test_01_recruiter_can_create_challenge(self):
        """1. A recruiter can create a challenge."""
        self.client.login(username='recruiter_alice', password='password123')
        response = self.client.post(reverse('challenges:recruiter_challenge_create'), {
            'title': 'PostgreSQL Optimization Challenge',
            'job': self.job.id,
            'challenge_type': Challenge.ChallengeType.DATABASE,
            'difficulty': Challenge.Difficulty.INTERMEDIATE,
            'description': 'Optimize database schemas and indexes',
            'problem_statement': 'Write optimal query execution plans',
            'maximum_marks': 100,
            'start_at': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'deadline': (timezone.now() + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
            'allowed_submission_formats': 'SQL, ZIP',
            'max_file_size_mb': 25,
            'status': Challenge.Status.PUBLISHED,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Challenge.objects.filter(title='PostgreSQL Optimization Challenge').exists())

    def test_02_recruiter_can_assign_challenge_to_selected_students(self):
        """2. A recruiter can assign a challenge to selected students."""
        self.client.login(username='recruiter_alice', password='password123')
        response = self.client.post(
            reverse('challenges:recruiter_challenge_assign', args=[self.challenge.id]),
            {'selected_applications': [self.application.id]}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ChallengeAssignment.objects.filter(
            challenge=self.challenge,
            student=self.student_profile_1
        ).exists())

    def test_03_only_assigned_students_can_view_challenge(self):
        """3. Only assigned students can view the challenge."""
        assignment = ChallengeAssignment.objects.create(
            challenge=self.challenge,
            student=self.student_profile_1,
            application=self.application,
            deadline=self.deadline,
            status=ChallengeAssignment.Status.ASSIGNED
        )
        self.client.login(username='student_arjun', password='password123')
        response = self.client.get(reverse('challenges:student_challenge_detail', args=[assignment.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Django REST API Challenge')

    def test_04_unassigned_student_cannot_access_challenge(self):
        """4. An unassigned student cannot access the challenge."""
        assignment = ChallengeAssignment.objects.create(
            challenge=self.challenge,
            student=self.student_profile_1,
            application=self.application,
            deadline=self.deadline,
            status=ChallengeAssignment.Status.ASSIGNED
        )
        # Login as student 2 who was never assigned
        self.client.login(username='student_bhavna', password='password123')
        response = self.client.get(reverse('challenges:student_challenge_detail', args=[assignment.id]))
        self.assertEqual(response.status_code, 403)

    def test_05_student_cannot_access_another_students_assignment_by_modifying_url(self):
        """5. A student cannot access another student's assignment by modifying the URL."""
        assignment_1 = ChallengeAssignment.objects.create(
            challenge=self.challenge,
            student=self.student_profile_1,
            deadline=self.deadline,
            status=ChallengeAssignment.Status.ASSIGNED
        )
        self.client.login(username='student_bhavna', password='password123')
        # Student Bhavna attempts to open Student Arjun's assignment ID
        response = self.client.get(reverse('challenges:student_challenge_detail', args=[assignment_1.id]))
        self.assertEqual(response.status_code, 403)

    def test_06_student_cannot_access_challenge_assigned_by_another_company_without_authorization(self):
        """6. A student cannot access a challenge assigned by another company without authorization."""
        challenge_b = Challenge.objects.create(
            recruiter=self.recruiter_profile_b,
            title='DataCore Secret AI Challenge',
            description='Private AI Test',
            problem_statement='Internal NLP benchmark',
            deadline=self.deadline,
            status=Challenge.Status.PUBLISHED
        )
        assignment_b = ChallengeAssignment.objects.create(
            challenge=challenge_b,
            student=self.student_profile_2, # assigned to Bhavna
            deadline=self.deadline,
            status=ChallengeAssignment.Status.ASSIGNED
        )
        # Arjun tries to access DataCore's assignment
        self.client.login(username='student_arjun', password='password123')
        response = self.client.get(reverse('challenges:student_challenge_detail', args=[assignment_b.id]))
        self.assertEqual(response.status_code, 403)

    def test_07_student_can_submit_eligible_solution(self):
        """7. A student can submit an eligible solution."""
        assignment = ChallengeAssignment.objects.create(
            challenge=self.challenge,
            student=self.student_profile_1,
            application=self.application,
            deadline=self.deadline,
            status=ChallengeAssignment.Status.IN_PROGRESS
        )
        self.client.login(username='student_arjun', password='password123')
        response = self.client.post(
            reverse('challenges:student_challenge_submit', args=[assignment.id]),
            {
                'description': 'Implemented REST API using Django REST Framework with Token Authentication and Redis rate limiting.',
                'repository_url': 'https://github.com/arjun/django-api-solution',
                'demonstration_url': 'https://arjun-api-demo.up.railway.app',
            }
        )
        self.assertEqual(response.status_code, 302)
        assignment.refresh_from_db()
        self.assertEqual(assignment.status, ChallengeAssignment.Status.SUBMITTED)
        self.assertTrue(ChallengeSubmission.objects.filter(assignment=assignment).exists())

    def test_08_student_cannot_submit_after_deadline_unless_extension_authorized(self):
        """8. A student cannot submit after the deadline unless an extension is authorized."""
        # Expired assignment
        past_deadline = timezone.now() - timedelta(hours=2)
        assignment = ChallengeAssignment.objects.create(
            challenge=self.challenge,
            student=self.student_profile_1,
            application=self.application,
            deadline=past_deadline,
            status=ChallengeAssignment.Status.IN_PROGRESS
        )
        self.client.login(username='student_arjun', password='password123')
        response = self.client.post(
            reverse('challenges:student_challenge_submit', args=[assignment.id]),
            {'description': 'Late submission attempt'}
        )
        self.assertEqual(response.status_code, 302)
        assignment.refresh_from_db()
        # Submission must NOT be created due to server-side cutoff
        self.assertEqual(assignment.status, ChallengeAssignment.Status.IN_PROGRESS)
        self.assertFalse(ChallengeSubmission.objects.filter(assignment=assignment).exists())

    def test_09_recruiter_can_view_submissions_for_their_own_challenges(self):
        """9. A recruiter can view submissions for their own challenges."""
        assignment = ChallengeAssignment.objects.create(
            challenge=self.challenge,
            student=self.student_profile_1,
            deadline=self.deadline,
            status=ChallengeAssignment.Status.SUBMITTED
        )
        submission = ChallengeSubmission.objects.create(
            assignment=assignment,
            description='Working solution code'
        )
        self.client.login(username='recruiter_alice', password='password123')
        response = self.client.get(reverse('challenges:recruiter_challenge_submissions', args=[self.challenge.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Working solution code')

    def test_10_recruiter_cannot_evaluate_another_recruiters_submission(self):
        """10. A recruiter cannot evaluate another recruiter's submission."""
        assignment = ChallengeAssignment.objects.create(
            challenge=self.challenge, # Company A
            student=self.student_profile_1,
            deadline=self.deadline,
            status=ChallengeAssignment.Status.SUBMITTED
        )
        submission = ChallengeSubmission.objects.create(
            assignment=assignment,
            description='Company A Candidate Solution'
        )
        # Login as Recruiter Bob from Company B
        self.client.login(username='recruiter_bob', password='password123')
        response = self.client.get(reverse('challenges:recruiter_submission_evaluate', args=[submission.id]))
        self.assertEqual(response.status_code, 403)

    def test_11_student_cannot_modify_evaluation(self):
        """11. A student cannot modify an evaluation."""
        assignment = ChallengeAssignment.objects.create(
            challenge=self.challenge,
            student=self.student_profile_1,
            deadline=self.deadline,
            status=ChallengeAssignment.Status.EVALUATED
        )
        submission = ChallengeSubmission.objects.create(
            assignment=assignment,
            description='My submission'
        )
        evaluation = ChallengeEvaluation.objects.create(
            submission=submission,
            evaluator=self.recruiter_user_a,
            total_marks=85,
            feedback='Good work on tests'
        )
        self.client.login(username='student_arjun', password='password123')
        # Student attempts to POST to the evaluate endpoint
        response = self.client.post(
            reverse('challenges:recruiter_submission_evaluate', args=[submission.id]),
            {'technical_correctness': 100}
        )
        self.assertEqual(response.status_code, 403)

    def test_12_revoked_assignments_no_longer_permit_access(self):
        """12. Revoked assignments no longer permit access."""
        assignment = ChallengeAssignment.objects.create(
            challenge=self.challenge,
            student=self.student_profile_1,
            deadline=self.deadline,
            status=ChallengeAssignment.Status.REVOKED,
            revoked_at=timezone.now(),
            revocation_reason='Candidate withdrew'
        )
        self.client.login(username='student_arjun', password='password123')
        # Attempt to submit solution for revoked assignment
        response = self.client.post(
            reverse('challenges:student_challenge_submit', args=[assignment.id]),
            {'description': 'Attempting to submit revoked assignment'}
        )
        self.assertEqual(response.status_code, 302)
        # Verify no submission was accepted
        self.assertFalse(ChallengeSubmission.objects.filter(assignment=assignment).exists())

    def test_13_duplicate_active_assignments_are_prevented(self):
        """13. Duplicate active assignments are prevented."""
        ChallengeAssignment.objects.create(
            challenge=self.challenge,
            student=self.student_profile_1,
            deadline=self.deadline,
            status=ChallengeAssignment.Status.ASSIGNED
        )
        self.client.login(username='recruiter_alice', password='password123')
        # Attempt to assign Arjun again to the same challenge
        self.client.post(
            reverse('challenges:recruiter_challenge_assign', args=[self.challenge.id]),
            {'selected_applications': [self.application.id]}
        )
        # Count must remain exactly 1
        active_count = ChallengeAssignment.objects.filter(
            challenge=self.challenge,
            student=self.student_profile_1
        ).count()
        self.assertEqual(active_count, 1)

    def test_14_evaluation_history_is_maintained(self):
        """14. Evaluation history is maintained."""
        assignment = ChallengeAssignment.objects.create(
            challenge=self.challenge,
            student=self.student_profile_1,
            deadline=self.deadline,
            status=ChallengeAssignment.Status.SUBMITTED
        )
        submission = ChallengeSubmission.objects.create(
            assignment=assignment,
            description='Candidate Solution for History'
        )
        self.client.login(username='recruiter_alice', password='password123')
        # Submit evaluation
        self.client.post(
            reverse('challenges:recruiter_submission_evaluate', args=[submission.id]),
            {
                'technical_correctness': 28,
                'code_quality': 25,
                'problem_solving': 20,
                'practical_implementation': 15,
                'documentation': 7,
                'feedback': 'Excellent structure and clean commit history.',
                'recommended_stage': ChallengeEvaluation.RecommendedStage.SCHEDULE_INTERVIEW,
                'evaluation_status': ChallengeEvaluation.EvaluationStatus.PUBLISHED
            }
        )
        self.assertTrue(ChallengeEvaluation.objects.filter(submission=submission).exists())
        eval_record = ChallengeEvaluation.objects.get(submission=submission)
        self.assertEqual(eval_record.total_marks, 95)
        # Check audit event logged
        self.assertTrue(ChallengeEvent.objects.filter(
            assignment=assignment,
            event_type=ChallengeEvent.EventType.EVALUATION_PUBLISHED
        ).exists())

    def test_15_recruitment_status_updates_correctly(self):
        """15. Recruitment status updates correctly."""
        assignment = ChallengeAssignment.objects.create(
            challenge=self.challenge,
            student=self.student_profile_1,
            application=self.application,
            deadline=self.deadline,
            status=ChallengeAssignment.Status.SUBMITTED
        )
        submission = ChallengeSubmission.objects.create(
            assignment=assignment,
            description='High Quality Candidate Solution'
        )
        self.client.login(username='recruiter_alice', password='password123')
        # Evaluate and advance to interview
        self.client.post(
            reverse('challenges:recruiter_submission_evaluate', args=[submission.id]),
            {
                'technical_correctness': 30,
                'code_quality': 25,
                'problem_solving': 20,
                'practical_implementation': 15,
                'documentation': 10,
                'feedback': 'Outstanding candidate! Ready for technical interview round.',
                'recommended_stage': ChallengeEvaluation.RecommendedStage.SCHEDULE_INTERVIEW,
                'evaluation_status': ChallengeEvaluation.EvaluationStatus.PUBLISHED
            }
        )
        self.application.refresh_from_db()
        self.assertEqual(self.application.status, Application.Status.INTERVIEW)

