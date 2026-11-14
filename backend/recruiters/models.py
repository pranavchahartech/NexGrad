from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify


class Company(models.Model):
    """
    Corporate organization hiring engineering talent.
    Supports both manually registered partners and automated public board discovery (e.g. Greenhouse).
    """
    class SourceProvider(models.TextChoices):
        MANUAL = 'MANUAL', 'Manually Registered'
        GREENHOUSE = 'GREENHOUSE', 'Greenhouse Job Board API'
        LEVER = 'LEVER', 'Lever Job Board'
        WORKDAY = 'WORKDAY', 'Workday API'
        OTHER = 'OTHER', 'Other Public Career Source'

    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    industry = models.CharField(max_length=100, default='Technology & Engineering')
    website = models.URLField(blank=True, max_length=500)
    logo_url = models.URLField(blank=True, max_length=500, help_text="Direct URL to company logo")
    career_page_url = models.URLField(blank=True, max_length=500, help_text="Official career portal URL")
    description = models.TextField(blank=True)
    headquarters = models.CharField(max_length=150, blank=True)
    company_size = models.CharField(max_length=50, default='50-250 Employees')
    source_provider = models.CharField(max_length=50, choices=SourceProvider.choices, default=SourceProvider.MANUAL)
    source_board_token = models.CharField(max_length=100, blank=True, help_text="Provider board token (e.g. cloudflare, github)")
    is_auto_generated = models.BooleanField(default=False, help_text="Imported automatically from external job board")
    is_verified = models.BooleanField(default=False, help_text="Formally verified company or claimed by official representative")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Companies'
        ordering = ['name']

    def __str__(self):
        tag = " [Auto-Imported]" if self.is_auto_generated else ""
        return f"{self.name}{tag}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or 'company'
            slug = base_slug
            counter = 1
            while Company.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def active_jobs_count(self):
        return self.jobs.filter(is_active=True).count()

    @property
    def active_internships_count(self):
        return self.internships.filter(is_active=True).count()

    @property
    def total_active_openings(self):
        return self.active_jobs_count + self.active_internships_count

    @property
    def primary_board(self):
        return self.boards.first()

    @property
    def primary_recruiter_profile(self):
        return self.recruiters.first()


class CompanyBoard(models.Model):
    """
    Tracks external job board feeds (e.g. Greenhouse boards-api.greenhouse.io/v1/boards/<board_token>).
    """
    class Provider(models.TextChoices):
        GREENHOUSE = 'GREENHOUSE', 'Greenhouse Job Board API'
        LEVER = 'LEVER', 'Lever API'
        WORKDAY = 'WORKDAY', 'Workday API'
        OTHER = 'OTHER', 'Other Public Source'

    class SyncStatus(models.TextChoices):
        IDLE = 'IDLE', 'Idle / Synced'
        SYNCING = 'SYNCING', 'Synchronization In Progress'
        SUCCESS = 'SUCCESS', 'Last Sync Succeeded'
        FAILED = 'FAILED', 'Last Sync Failed'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='boards')
    provider = models.CharField(max_length=50, choices=Provider.choices, default=Provider.GREENHOUSE)
    board_token = models.CharField(max_length=100, unique=True, help_text="Public board identifier, e.g. cloudflare, github, stripe")
    api_endpoint = models.URLField(max_length=500, blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    sync_status = models.CharField(max_length=30, choices=SyncStatus.choices, default=SyncStatus.IDLE)
    error_message = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.company.name} ({self.get_provider_display()} -> {self.board_token})"


class RecruiterProfile(models.Model):
    """
    Recruiter account linked to an employer company.
    Supports both platform-generated automated channel profiles and verified human recruiters.
    """
    class VerificationStatus(models.TextChoices):
        UNVERIFIED = 'UNVERIFIED', 'Auto-generated — Unverified'
        PENDING_REVIEW = 'PENDING_REVIEW', 'Claim Pending Review'
        VERIFIED = 'VERIFIED', 'Verified Company Profile'
        CLAIMED = 'CLAIMED', 'Claimed & Verified by Representative'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='recruiter_profile')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='recruiters')
    designation = models.CharField(max_length=100, default='Talent Acquisition Lead')
    department = models.CharField(max_length=100, blank=True, default='Engineering Hiring')
    
    # Auto-generation and Verification fields
    is_auto_generated = models.BooleanField(default=False, help_text="True if automatically created by external importer")
    verification_status = models.CharField(
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNVERIFIED,
        help_text="Verification tier of this recruiter account"
    )
    internal_identifier = models.CharField(
        max_length=64,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique internal platform identifier (e.g. AUTO-REC-XXXX)"
    )
    is_verified = models.BooleanField(default=False)
    claimed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='claimed_recruiter_profiles',
        help_text="Authorized human user who claimed this auto-generated recruiter profile"
    )
    claimed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        comp = self.company.name if self.company else 'Unassigned'
        auto = " [Auto-Recruiter]" if self.is_auto_generated else ""
        return f"{name} ({comp}){auto}"

    @property
    def display_status(self):
        if self.is_auto_generated and self.verification_status == self.VerificationStatus.UNVERIFIED:
            return "Auto-generated — Unverified"
        return self.get_verification_status_display()


class CompanyVerification(models.Model):
    """
    Official claim and verification requests submitted by company representatives
    to take ownership of auto-generated recruiter profiles.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Administrator Review'
        APPROVED = 'APPROVED', 'Claim Approved & Ownership Granted'
        REJECTED = 'REJECTED', 'Claim Rejected'

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='verification_claims')
    recruiter_profile = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE, related_name='verification_claims')
    claimant_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submitted_company_claims')
    work_email = models.EmailField(help_text="Official corporate email address (e.g. name@company.com)")
    official_designation = models.CharField(max_length=150, help_text="Official title at the company")
    claim_statement = models.TextField(help_text="Explanation of authority to represent the company on CareerForge")
    proof_link = models.URLField(blank=True, max_length=500, help_text="Link to verified LinkedIn, corporate directory, or domain proof")
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    
    # Audit trail
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='decided_claims')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True, help_text="Notes from administrator on verification decision")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Claim for {self.company.name} by {self.work_email} [{self.get_status_display()}]"


class DataImportLog(models.Model):
    """
    Detailed audit log of external job board discovery and synchronization executions.
    """
    class Status(models.TextChoices):
        SUCCESS = 'SUCCESS', 'Completed Successfully'
        PARTIAL = 'PARTIAL', 'Completed with Warnings/Skipped Records'
        FAILED = 'FAILED', 'Failed / Error'

    provider = models.CharField(max_length=50, default='GREENHOUSE')
    board_token = models.CharField(max_length=100)
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='import_logs')
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.SUCCESS)
    jobs_discovered = models.PositiveIntegerField(default=0)
    jobs_created = models.PositiveIntegerField(default=0)
    jobs_updated = models.PositiveIntegerField(default=0)
    jobs_deactivated = models.PositiveIntegerField(default=0)
    internships_created = models.PositiveIntegerField(default=0)
    log_output = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"Import [{self.provider}/{self.board_token}] - {self.get_status_display()} ({self.jobs_discovered} found)"
