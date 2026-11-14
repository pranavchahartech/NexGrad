from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from jobs.models import Job, Skill
from recruiters.models import Company, RecruiterProfile
from students.models import StudentProfile
from applications.models import Application

class NexgradPlatformTests(TestCase):
    """
    Automated test suite fulfilling the INT253 30-mark academic evaluation requirements.
    Tests URL routing, MVT template rendering, model constraints, and JSON endpoints.
    """

    def setUp(self):
        self.client = Client()

        # Create test company and recruiter
        self.company = Company.objects.create(
            name='Test Tech Labs',
            slug='test-tech-labs',
            industry='Software',
            headquarters='Bengaluru'
        )
        self.recruiter_user = CustomUser.objects.create_user(
            username='testrecruiter',
            email='recruiter@test.com',
            password='testpassword123',
            role=CustomUser.Role.RECRUITER
        )
        self.recruiter_profile = RecruiterProfile.objects.create(
            user=self.recruiter_user,
            company=self.company
        )

        # Create skill and job
        self.skill = Skill.objects.create(name='Python Testing', category='BACKEND')
        self.job = Job.objects.create(
            recruiter=self.recruiter_profile,
            company=self.company,
            title='Software Development Engineer 1',
            job_type='FULL_TIME',
            location='Bengaluru',
            description='Test job description',
            min_cgpa=7.0
        )
        self.job.required_skills.add(self.skill)

        # Create test student
        self.student_user = CustomUser.objects.create_user(
            username='teststudent',
            email='student@test.edu',
            password='testpassword123',
            role=CustomUser.Role.STUDENT
        )
        self.student_profile = StudentProfile.objects.create(
            user=self.student_user,
            branch='CSE',
            cgpa=8.5
        )

    def test_01_homepage_loads_successfully(self):
        """1. Homepage loads with status code 200 and brand name."""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nexgrad')
        self.assertContains(response, 'Build Your Engineering')
        self.assertContains(response, 'Take Assessments')

    def test_02_job_list_view_and_search(self):
        """2. Job list view renders and search filter returns matching jobs."""
        response = self.client.get(reverse('jobs:list') + '?q=Software')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Software Development Engineer 1')

    def test_03_job_detail_valid_and_invalid_id(self):
        """3. Valid job ID returns 200, invalid job ID returns 404."""
        response_valid = self.client.get(reverse('jobs:detail', args=[self.job.id]))
        self.assertEqual(response_valid.status_code, 200)
        self.assertContains(response_valid, 'Software Development Engineer 1')

        response_invalid = self.client.get(reverse('jobs:detail', args=[99999]))
        self.assertEqual(response_invalid.status_code, 404)

    def test_04_json_api_opportunities_endpoint(self):
        """4. REST API endpoint returns valid JSON with count and status."""
        response = self.client.get(reverse('jobs:api_opportunities'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['platform'], 'Nexgrad Career Intelligence')
        self.assertTrue(len(data['opportunities']) >= 1)

    def test_05_student_registration(self):
        """5. Student registration creates user with STUDENT role."""
        response = self.client.post(reverse('accounts:register_student'), {
            'username': 'newstudent',
            'first_name': 'Rohan',
            'last_name': 'Kumar',
            'email': 'rohan@university.edu',
            'password1': 'SecurePassword@123',
            'password2': 'SecurePassword@123',
        })
        new_user = CustomUser.objects.filter(username='newstudent').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.role, CustomUser.Role.STUDENT)

    def test_06_prevent_duplicate_application(self):
        """6. Database constraint prevents duplicate student applications to same job."""
        self.client.login(username='teststudent', password='testpassword123')

        # First application
        app = Application.objects.create(
            student=self.student_profile,
            job=self.job,
            status=Application.Status.APPLIED
        )
        self.assertIsNotNone(app.id)

        # Attempt duplicate application via view
        response = self.client.post(reverse('applications:apply_to_job', args=[self.job.id]), {
            'cover_letter': 'Duplicate attempt'
        })
        # Should be redirected with warning, not create duplicate
        self.assertEqual(Application.objects.filter(student=self.student_profile, job=self.job).count(), 1)

    def test_07_custom_404_page(self):
        """7. Non-existent URL triggers custom 404 error page."""
        response = self.client.get('/this-path-does-not-exist-anywhere/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'errors/404.html')

    def test_08_developer_api_docs_page(self):
        """8. Developer & Partner API documentation portal loads with 200 OK."""
        response = self.client.get(reverse('core:api_docs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enterprise Partner & Developer API')
        self.assertContains(response, '/jobs/api/opportunities/')
        self.assertTemplateUsed(response, 'core/api_docs.html')
