from django.db import models
from django.conf import settings
from institutions.models import Institution, Department

class StudentProfile(models.Model):
    BRANCH_CHOICES = (
        ('CSE', 'Computer Science & Engineering'),
        ('ECE', 'Electronics & Communication'),
        ('EE', 'Electrical Engineering'),
        ('ME', 'Mechanical Engineering'),
        ('CE', 'Civil Engineering'),
        ('IT', 'Information Technology'),
        ('AI_DS', 'Artificial Intelligence & Data Science'),
    )

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.CharField(max_length=50, choices=BRANCH_CHOICES, default='CSE')
    degree = models.CharField(max_length=50, default='B.Tech')
    graduation_year = models.PositiveIntegerField(default=2026)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=8.00)
    headline = models.CharField(max_length=150, blank=True, default='Engineering Student | Aspiring Software Engineer')
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True, default='India')
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.branch} '{str(self.graduation_year)[-2:]})"

    @property
    def completion_percentage(self):
        """Calculates dynamic profile completion percentage."""
        score = 20 # User account exists
        if self.headline: score += 15
        if self.bio: score += 15
        if self.institution: score += 10
        if self.github_url or self.portfolio_url: score += 15
        if self.resumes.exists(): score += 15
        if self.projects.exists(): score += 10
        return min(score, 100)

class Resume(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=100, default='Primary Technical Resume')
    file = models.FileField(upload_to='resumes/')
    is_default = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.student.user.username}"

class Project(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=150)
    description = models.TextField()
    technologies = models.CharField(max_length=200, help_text="e.g. Python, Django, PostgreSQL, Docker")
    repo_url = models.URLField(blank=True, help_text="GitHub/GitLab repository URL")
    live_url = models.URLField(blank=True, help_text="Live demo or deployment link")
    contribution_summary = models.TextField(blank=True, help_text="Individual responsibilities and achievements")
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.student.user.username})"

class StudentSkill(models.Model):
    LEVEL_CHOICES = (
        ('BEGINNER', 'Beginner'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    proficiency = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='INTERMEDIATE')
    is_verified = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'skill_name')

    def __str__(self):
        return f"{self.skill_name} ({self.proficiency}) - {self.student.user.username}"

