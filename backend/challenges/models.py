from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from recruiters.models import RecruiterProfile
from jobs.models import Job
from students.models import StudentProfile
from applications.models import Application

class Challenge(models.Model):
    """
    Recruiter-created private technical challenge / assignment.
    Strictly private: never shown in public listings or unauthenticated endpoints.
    """
    class ChallengeType(models.TextChoices):
        CODING = 'CODING', 'Coding Challenge'
        PROGRAMMING = 'PROGRAMMING', 'Programming Problem'
        WEB_DEV = 'WEB_DEV', 'Web Development Assignment'
        DATABASE = 'DATABASE', 'Database Design Task'
        DEBUGGING = 'DEBUGGING', 'Debugging Challenge'
        KNOWLEDGE = 'KNOWLEDGE', 'Technical Knowledge Assessment'
        ARCHITECTURE = 'ARCHITECTURE', 'Software Architecture Case Study'
        COMPANY_PROBLEM = 'COMPANY_PROBLEM', 'Real-World Company Problem'
        ENGINEERING = 'ENGINEERING', 'Practical Engineering Assignment'
        PROJECT = 'PROJECT', 'Project Development Task'

    class Difficulty(models.TextChoices):
        BEGINNER = 'BEGINNER', 'Foundational / Junior'
        INTERMEDIATE = 'INTERMEDIATE', 'Mid-Level Practitioner'
        ADVANCED = 'ADVANCED', 'Senior / Architecture Level'
        EXPERT = 'EXPERT', 'Principal / Specialized'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft (Unpublished)'
        PUBLISHED = 'PUBLISHED', 'Published & Active'
        ARCHIVED = 'ARCHIVED', 'Archived / Closed'

    recruiter = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE, related_name='challenges')
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True, related_name='challenges', help_text="Associated job vacancy")
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=230, blank=True)
    challenge_type = models.CharField(max_length=40, choices=ChallengeType.choices, default=ChallengeType.CODING)
    description = models.TextField(help_text="Overview and business context for the candidate")
    problem_statement = models.TextField(help_text="Detailed problem requirements and expectations")
    instructions = models.TextField(blank=True, help_text="Step-by-step submission instructions & constraints")
    technical_requirements = models.TextField(blank=True, help_text="e.g. Django 5.x, PostgreSQL, clean architecture, unit tests")
    required_skills = models.CharField(max_length=255, blank=True, help_text="Comma-separated skill tags, e.g. Python, REST APIs, Docker")
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.INTERMEDIATE)
    input_output_specs = models.TextField(blank=True, help_text="Input/Output specifications, test cases, or data schemas where applicable")
    reference_materials = models.TextField(blank=True, help_text="Documentation links, API specs, or reference repos")
    maximum_marks = models.PositiveIntegerField(default=100)
    evaluation_criteria = models.JSONField(default=dict, blank=True, help_text="Configurable evaluation criteria breakdown as JSON or key-value pairs")
    start_at = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField(help_text="Final submission cutoff")
    time_limit_minutes = models.PositiveIntegerField(null=True, blank=True, help_text="Optional time limit in minutes once started")
    allowed_submission_formats = models.CharField(max_length=255, default='Source Code, ZIP, PDF Report, GitHub Repository, Live Demo URL')
    max_file_size_mb = models.PositiveIntegerField(default=25)
    allow_resubmission = models.BooleanField(default=False)
    maximum_submissions = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        job_tag = f" [{self.job.title}]" if self.job else ""
        return f"{self.title}{job_tag} - {self.recruiter.company.name if self.recruiter.company else 'Recruiter'}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title) or 'challenge'
            unique_slug = base_slug
            counter = 1
            while Challenge.objects.filter(slug=unique_slug).exclude(pk=self.pk).exists():
                unique_slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)

    @property
    def role_title(self):
        return self.job.title if self.job else "Engineering Position"

    @property
    def is_expired(self):
        return timezone.now() > self.deadline

    @property
    def assigned_count(self):
        return self.assignments.exclude(status=ChallengeAssignment.Status.REVOKED).count()

    @property
    def submission_count(self):
        return ChallengeSubmission.objects.filter(assignment__challenge=self).count()

    @property
    def evaluated_count(self):
        return self.assignments.filter(status=ChallengeAssignment.Status.EVALUATED).count()


class ChallengeAttachment(models.Model):
    """
    Supporting documents, problem assets, starter code or specs attached to a challenge.
    """
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='challenge_attachments/')
    title = models.CharField(max_length=150)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.challenge.title})"


class ChallengeAssignment(models.Model):
    """
    Explicit, private relationship giving a specific candidate access to a challenge.
    A candidate can ONLY see and submit challenges for which they hold an active assignment.
    """
    class Status(models.TextChoices):
        ASSIGNED = 'ASSIGNED', 'Assigned'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        EVALUATED = 'EVALUATED', 'Evaluated'
        REVOKED = 'REVOKED', 'Revoked'

    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='assignments')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='challenge_assignments')
    application = models.ForeignKey(Application, on_delete=models.SET_NULL, null=True, blank=True, related_name='challenge_assignments')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assigned_challenges')
    assigned_at = models.DateTimeField(auto_now_add=True)
    available_from = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField(help_text="Candidate-specific deadline (defaults to challenge deadline, extendable by recruiter)")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ASSIGNED)
    started_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='revoked_assignments')
    revocation_reason = models.TextField(blank=True)

    class Meta:
        ordering = ['-assigned_at']
        constraints = [
            models.UniqueConstraint(
                fields=['challenge', 'student'],
                condition=models.Q(status__in=['ASSIGNED', 'IN_PROGRESS', 'SUBMITTED', 'UNDER_REVIEW', 'EVALUATED']),
                name='unique_active_challenge_assignment'
            )
        ]

    def __str__(self):
        return f"{self.student.user.username} -> {self.challenge.title} [{self.get_status_display()}]"

    def save(self, *args, **kwargs):
        if not self.deadline and self.challenge_id:
            self.deadline = self.challenge.deadline
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        return self.status != self.Status.REVOKED

    @property
    def is_deadline_passed(self):
        return timezone.now() > self.deadline

    @property
    def latest_submission(self):
        return self.submissions.order_by('-submission_number').first()

    @property
    def time_remaining_display(self):
        now = timezone.now()
        if now >= self.deadline:
            return "Deadline Passed"
        diff = self.deadline - now
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        if days > 0:
            return f"{days}d {hours}h remaining"
        elif hours > 0:
            return f"{hours}h {minutes}m remaining"
        else:
            return f"{minutes}m remaining"


class ChallengeSubmission(models.Model):
    """
    Candidate solution submission containing code, repository links, documentation, and notes.
    """
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        EVALUATED = 'EVALUATED', 'Evaluated'

    assignment = models.ForeignKey(ChallengeAssignment, on_delete=models.CASCADE, related_name='submissions')
    submission_number = models.PositiveIntegerField(default=1)
    description = models.TextField(help_text="Solution overview, architectural decisions, and setup instructions")
    uploaded_file = models.FileField(upload_to='challenge_submissions/', null=True, blank=True, help_text="Source code or ZIP package")
    repository_url = models.URLField(blank=True, help_text="Public or shared GitHub/GitLab repository link")
    demonstration_url = models.URLField(blank=True, help_text="Deployed live demonstration URL")
    supporting_document = models.FileField(upload_to='challenge_docs/', null=True, blank=True, help_text="Architecture PDF or technical documentation")
    additional_comments = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Submission #{self.submission_number} for {self.assignment.challenge.title} by {self.assignment.student.user.username}"


class ChallengeEvaluation(models.Model):
    """
    Recruiter evaluation record containing multi-criteria marks, written feedback, and stage recommendations.
    """
    class RecommendedStage(models.TextChoices):
        SCHEDULE_INTERVIEW = 'SCHEDULE_INTERVIEW', 'Advance to Technical Interview'
        SHORTLIST_NEXT_ROUND = 'SHORTLIST_NEXT_ROUND', 'Advance to Subsequent Challenge'
        OFFER_POSITION = 'OFFER_POSITION', 'Direct Offer Recommendation'
        REQUEST_REVISION = 'REQUEST_REVISION', 'Request Revision / Corrections'
        NOT_RECOMMENDED = 'NOT_RECOMMENDED', 'Reject / Do Not Proceed'

    class EvaluationStatus(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft (Private to Recruiter)'
        PUBLISHED = 'PUBLISHED', 'Published to Candidate'

    submission = models.OneToOneField(ChallengeSubmission, on_delete=models.CASCADE, related_name='evaluation')
    evaluator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='challenge_evaluations')
    technical_correctness = models.PositiveIntegerField(default=0, help_text="Marks for functionality & test cases")
    code_quality = models.PositiveIntegerField(default=0, help_text="Marks for readability, patterns, & maintainability")
    problem_solving = models.PositiveIntegerField(default=0, help_text="Marks for algorithmic complexity & logic")
    practical_implementation = models.PositiveIntegerField(default=0, help_text="Marks for database/API implementation")
    documentation = models.PositiveIntegerField(default=0, help_text="Marks for setup docs & explanation")
    criteria_scores = models.JSONField(default=dict, blank=True, help_text="Configurable criteria marks mapping")
    total_marks = models.PositiveIntegerField(default=0)
    feedback = models.TextField(help_text="Detailed feedback visible to candidate when published")
    strengths = models.TextField(blank=True, help_text="Observed strengths in candidate solution")
    areas_for_improvement = models.TextField(blank=True, help_text="Constructive suggestions for growth")
    internal_recruiter_notes = models.TextField(blank=True, help_text="Private hiring team notes (never visible to candidate)")
    recommended_stage = models.CharField(max_length=30, choices=RecommendedStage.choices, default=RecommendedStage.SCHEDULE_INTERVIEW)
    evaluation_status = models.CharField(max_length=20, choices=EvaluationStatus.choices, default=EvaluationStatus.PUBLISHED)
    evaluated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-evaluated_at']

    def __str__(self):
        return f"Evaluation: {self.total_marks}/{self.submission.assignment.challenge.maximum_marks} for {self.submission.assignment.student.user.username}"


class ChallengeEvent(models.Model):
    """
    Immutable audit trail logging all lifecycle events for candidate challenges.
    """
    class EventType(models.TextChoices):
        CHALLENGE_CREATED = 'CHALLENGE_CREATED', 'Challenge Created'
        CHALLENGE_PUBLISHED = 'CHALLENGE_PUBLISHED', 'Challenge Published'
        CANDIDATE_SELECTED = 'CANDIDATE_SELECTED', 'Candidate Shortlisted'
        CHALLENGE_ASSIGNED = 'CHALLENGE_ASSIGNED', 'Challenge Assigned to Candidate'
        ASSIGNMENT_REVOKED = 'ASSIGNMENT_REVOKED', 'Assignment Revoked'
        CHALLENGE_STARTED = 'CHALLENGE_STARTED', 'Challenge Started by Candidate'
        SUBMISSION_UPLOADED = 'SUBMISSION_UPLOADED', 'Solution Submitted'
        SUBMISSION_UPDATED = 'SUBMISSION_UPDATED', 'Solution Resubmitted'
        EVALUATION_SAVED = 'EVALUATION_SAVED', 'Evaluation Saved as Draft'
        EVALUATION_PUBLISHED = 'EVALUATION_PUBLISHED', 'Evaluation Published'
        RECRUITMENT_STATUS_CHANGED = 'RECRUITMENT_STATUS_CHANGED', 'Recruitment Status Changed'

    assignment = models.ForeignKey(ChallengeAssignment, on_delete=models.CASCADE, related_name='events')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='challenge_events')
    event_type = models.CharField(max_length=35, choices=EventType.choices)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.get_event_type_display()}] on {self.assignment} at {self.created_at}"

