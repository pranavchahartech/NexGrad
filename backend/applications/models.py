from django.db import models
from django.conf import settings
from students.models import StudentProfile, Resume
from jobs.models import Job, Internship

class Application(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        APPLIED = 'APPLIED', 'Applied'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
        ASSESSMENT = 'ASSESSMENT', 'Technical Assessment'
        INTERVIEW = 'INTERVIEW', 'Interview Scheduled'
        SELECTED = 'SELECTED', 'Offer Extended'
        REJECTED = 'REJECTED', 'Not Selected'
        WITHDRAWN = 'WITHDRAWN', 'Withdrawn'
        OFFER_ACCEPTED = 'OFFER_ACCEPTED', 'Offer Accepted'

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='applications')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications', null=True, blank=True)
    internship = models.ForeignKey(Internship, on_delete=models.CASCADE, related_name='applications', null=True, blank=True)
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True)
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.APPLIED)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'job'],
                condition=models.Q(job__isnull=False),
                name='unique_student_job_application'
            ),
            models.UniqueConstraint(
                fields=['student', 'internship'],
                condition=models.Q(internship__isnull=False),
                name='unique_student_internship_application'
            )
        ]

    @property
    def role_title(self):
        if self.job:
            return self.job.title
        elif self.internship:
            return f"{self.internship.title} (Internship)"
        return "Engineering Role"

    @property
    def company_name(self):
        if self.job:
            return self.job.company.name
        elif self.internship:
            return self.internship.company.name
        return "Hiring Partner"

    def __str__(self):
        target = self.role_title
        return f"{self.student.user.username} -> {target} [{self.get_status_display()}]"

class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='status_history')
    from_status = models.CharField(max_length=30)
    to_status = models.CharField(max_length=30)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Application status histories'

    def __str__(self):
        return f"Transition to {self.to_status} at {self.timestamp}"

class Interview(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    round_name = models.CharField(max_length=100, default='Technical Round 1 (System Architecture & Coding)')
    scheduled_time = models.DateTimeField()
    meeting_link = models.URLField(default='https://meet.google.com/nex-grad-room')
    interviewer = models.CharField(max_length=100, blank=True, default='Technical Lead')
    instructions = models.TextField(blank=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['scheduled_time']

    def __str__(self):
        return f"{self.round_name} - {self.application.student.user.username}"

