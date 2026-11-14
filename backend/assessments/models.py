from django.db import models
from students.models import StudentProfile

class Assessment(models.Model):
    DIFFICULTY_CHOICES = (
        ('BEGINNER', 'Foundational'),
        ('INTERMEDIATE', 'Intermediate Practitioner'),
        ('ADVANCED', 'Advanced Systems & Architecture'),
    )

    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, default='Python & Backend Systems')
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='INTERMEDIATE')
    duration_minutes = models.PositiveIntegerField(default=45)
    total_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=60)
    description = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_difficulty_display()})"

class AssessmentAttempt(models.Model):
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='attempts')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='assessment_attempts')
    score = models.PositiveIntegerField(default=0)
    is_passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.assessment.title}: {self.score}%"

class DeviceTelemetry(models.Model):
    """
    Experimental data model supporting Part 9 research:
    'Device-Neutral Assessment Runtime & Measurement Equivalence'
    Captures non-invasive execution telemetry for measurement comparison.
    """
    attempt = models.OneToOneField(AssessmentAttempt, on_delete=models.CASCADE, related_name='telemetry')
    viewport_width = models.PositiveIntegerField(default=1920)
    viewport_height = models.PositiveIntegerField(default=1080)
    input_modality = models.CharField(max_length=50, default='Keyboard + Mouse')
    interaction_count = models.PositiveIntegerField(default=0)
    round_trip_latency_ms = models.PositiveIntegerField(default=45)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Telemetry: {self.input_modality} ({self.viewport_width}x{self.viewport_height})"

