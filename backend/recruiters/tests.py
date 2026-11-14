from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from recruiters.models import Company, CompanyBoard, RecruiterProfile, CompanyVerification, DataImportLog
from recruiters.services.greenhouse_importer import GreenhouseJobBoardImporter
from jobs.models import Job, Internship, ExternalListing

User = get_user_model()


class GreenhouseImporterTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin_test',
            email='admin@careerforge.test',
            password='testpassword123',
            role=User.Role.ADMIN
        )
        self.claimant_user = User.objects.create_user(
            username='rep_sarah',
            email='sarah@cloudflare.corp',
            password='testpassword123',
            role=User.Role.RECRUITER
        )

    def test_01_greenhouse_importer_creates_company_and_recruiter_account(self):
        """Verifies company, recruiter account, and profile auto-provisioning."""
        importer = GreenhouseJobBoardImporter()
        res = importer.import_board('cloudflare')

        self.assertTrue(res['success'])
        self.assertTrue(res['is_new_company'])
        self.assertTrue(res['is_new_recruiter'])

        # Company check
        company = res['company']
        self.assertEqual(company.name, 'Cloudflare')
        self.assertEqual(company.source_provider, Company.SourceProvider.GREENHOUSE)
        self.assertEqual(company.source_board_token, 'cloudflare')
        self.assertTrue(company.is_auto_generated)
        self.assertFalse(company.is_verified)

        # Recruiter User check
        recruiter_user = res['recruiter_user']
        self.assertEqual(recruiter_user.role, User.Role.RECRUITER)
        self.assertTrue(recruiter_user.username.startswith('recruiter_cloudflare'))
        self.assertFalse(recruiter_user.is_verified)

        # Recruiter Profile check
        profile = res['recruiter_profile']
        self.assertEqual(profile.company, company)
        self.assertTrue(profile.is_auto_generated)
        self.assertEqual(profile.verification_status, RecruiterProfile.VerificationStatus.UNVERIFIED)
        self.assertEqual(profile.display_status, 'Auto-generated — Unverified')
        self.assertTrue(profile.internal_identifier.startswith('AUTO-REC-'))

        # Board and Log check
        board = CompanyBoard.objects.get(board_token='cloudflare')
        self.assertEqual(board.company, company)
        self.assertEqual(board.sync_status, CompanyBoard.SyncStatus.SUCCESS)

        log = DataImportLog.objects.get(id=res['log_id'])
        self.assertEqual(log.status, DataImportLog.Status.SUCCESS)
        self.assertGreater(log.jobs_discovered, 0)

    def test_02_duplicate_prevention_on_repeated_sync(self):
        """Verifies idempotent synchronization without duplicate companies or accounts."""
        importer = GreenhouseJobBoardImporter()
        res1 = importer.import_board('github')
        self.assertTrue(res1['is_new_company'])
        self.assertTrue(res1['is_new_recruiter'])

        # Re-syncing same board
        res2 = importer.import_board('github')
        self.assertFalse(res2['is_new_company'])
        self.assertFalse(res2['is_new_recruiter'])

        # Assert exactly 1 company and 1 recruiter account exists
        self.assertEqual(Company.objects.filter(source_board_token='github').count(), 1)
        self.assertEqual(RecruiterProfile.objects.filter(company=res1['company']).count(), 1)

    def test_03_jobs_and_internships_differentiation(self):
        """Verifies accurate categorization of full-time engineering roles vs internships."""
        importer = GreenhouseJobBoardImporter()
        res = importer.import_board('cloudflare')
        company = res['company']

        # Cloudflare fixture has both jobs and internships
        internships = Internship.objects.filter(company=company)
        jobs = Job.objects.filter(company=company)

        self.assertGreater(jobs.count(), 0)
        self.assertGreater(internships.count(), 0)

        # Verify external import flags
        for j in jobs:
            self.assertTrue(j.is_external_import)
            self.assertEqual(j.external_source, 'GREENHOUSE')
            self.assertTrue(j.external_id)
            self.assertTrue(j.external_apply_url)

        for i in internships:
            self.assertTrue(i.is_external_import)
            self.assertEqual(i.external_source, 'GREENHOUSE')

        # Check ExternalListing mapping
        self.assertEqual(ExternalListing.objects.filter(company=company).count(), jobs.count() + internships.count())

    def test_04_sync_deactivates_expired_listings(self):
        """Verifies listings removed from source payload are deactivated rather than deleted."""
        importer = GreenhouseJobBoardImporter()
        res = importer.import_board('figma')
        company = res['company']

        # Create a mock listing that will not be in the next payload
        stale_job = Job.objects.create(
            recruiter=res['recruiter_profile'],
            company=company,
            title='Obsolete Legacy Role',
            is_active=True,
            is_external_import=True,
            external_source='GREENHOUSE',
            external_id='9999999'
        )
        ExternalListing.objects.create(
            company=company,
            recruiter=res['recruiter_profile'],
            source_provider='GREENHOUSE',
            external_id='9999999',
            title='Obsolete Legacy Role',
            job=stale_job,
            is_active=True
        )

        # Trigger sync again
        sync_res = importer.import_board('figma')
        self.assertGreaterEqual(sync_res['jobs_deactivated'], 1)

        # Stale job should be marked is_active=False
        stale_job.refresh_from_db()
        self.assertFalse(stale_job.is_active)

    def test_05_admin_discovery_view_and_trigger_import(self):
        """Verifies administrator control center access and board ingestion endpoint."""
        # Non-admin access denied
        self.client.force_login(self.claimant_user)
        resp_denied = self.client.get(reverse('recruiters:admin_discovery'))
        self.assertEqual(resp_denied.status_code, 403)

        # Admin access granted
        self.client.force_login(self.admin_user)
        resp_admin = self.client.get(reverse('recruiters:admin_discovery'))
        self.assertEqual(resp_admin.status_code, 200)
        self.assertContains(resp_admin, "Company Discovery &amp; Recruiter Account Management")

        # Admin triggers import
        resp_post = self.client.post(reverse('recruiters:admin_trigger_import'), {
            'board_token': 'stripe'
        }, follow=True)
        self.assertEqual(resp_post.status_code, 200)
        self.assertTrue(Company.objects.filter(source_board_token='stripe').exists())

    def test_06_company_claim_and_verification_workflow(self):
        """Verifies complete account claim submission and administrator decision flow."""
        importer = GreenhouseJobBoardImporter()
        res = importer.import_board('datadog')
        company = res['company']
        profile = res['recruiter_profile']

        # Claimant user submits claim
        self.client.force_login(self.claimant_user)
        claim_url = reverse('recruiters:claim_company_account', kwargs={'company_slug': company.slug})
        resp_claim = self.client.post(claim_url, {
            'work_email': 'sarah.lead@datadoghq.com',
            'official_designation': 'VP of Engineering Talent',
            'claim_statement': 'I am the authorized recruitment director representing Datadog.',
            'proof_link': 'https://linkedin.com/in/sarah-talent-lead'
        }, follow=True)
        self.assertEqual(resp_claim.status_code, 200)

        # Verify claim in database
        claim = CompanyVerification.objects.get(company=company)
        self.assertEqual(claim.status, CompanyVerification.Status.PENDING)
        self.assertEqual(claim.work_email, 'sarah.lead@datadoghq.com')

        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, RecruiterProfile.VerificationStatus.PENDING_REVIEW)

        # Admin approves claim
        self.client.force_login(self.admin_user)
        approve_url = reverse('recruiters:admin_decide_claim', kwargs={'claim_id': claim.id, 'decision': 'approve'})
        resp_approve = self.client.post(approve_url, {'admin_notes': 'Corporate domain verified.'}, follow=True)
        self.assertEqual(resp_approve.status_code, 200)

        # Verify ownership transferred and status updated
        claim.refresh_from_db()
        self.assertEqual(claim.status, CompanyVerification.Status.APPROVED)
        self.assertEqual(claim.reviewed_by, self.admin_user)

        profile.refresh_from_db()
        self.assertEqual(profile.verification_status, RecruiterProfile.VerificationStatus.CLAIMED)
        self.assertTrue(profile.is_verified)
        self.assertEqual(profile.claimed_by, self.claimant_user)

        company.refresh_from_db()
        self.assertTrue(company.is_verified)

    def test_07_recruiter_dashboard_renders_clean_partner_workspace(self):
        """Verifies company recruiter dashboard renders clean partner workspace without unwanted comments."""
        importer = GreenhouseJobBoardImporter()
        res = importer.import_board('figma')
        company = res['company']
        recruiter_user = res['recruiter_user']

        # Log in as the recruiter user
        self.client.force_login(recruiter_user)
        resp = self.client.get(reverse('recruiters:dashboard'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Recruiter Workspace &amp; Pipeline")
        self.assertContains(resp, "Verified Partner")
        self.assertContains(resp, "Figma")

