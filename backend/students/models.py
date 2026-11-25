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
    profile_picture = models.ImageField(upload_to='profiles/avatars/', null=True, blank=True)
    phone = models.CharField(max_length=25, blank=True, default='')
    address = models.TextField(blank=True, default='')
    
    # College / Higher Education
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    college_name = models.CharField(max_length=200, blank=True, default='', help_text="College or University name")
    degree = models.CharField(max_length=100, blank=True, default='', help_text="Course or Degree e.g. B.Tech, BCA, MCA, B.Sc")
    branch = models.CharField(max_length=100, blank=True, default='', help_text="Branch or Specialization e.g. Computer Science")
    graduation_year = models.PositiveIntegerField(null=True, blank=True, help_text="Expected or actual year of graduation")
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, help_text="Current CGPA or score out of 10")
    
    # School Education
    school_name = models.CharField(max_length=200, blank=True, default='', help_text="School / Higher Secondary institution")
    school_marks = models.CharField(max_length=50, blank=True, default='', help_text="Overall School / Board marks or percentage")
    tenth_marks = models.CharField(max_length=50, blank=True, default='', help_text="10th Marks / Percentage")
    twelfth_marks = models.CharField(max_length=50, blank=True, default='', help_text="12th / Intermediate Marks")

    # Professional Summary & Links
    headline = models.CharField(max_length=150, blank=True, default='')
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True, default='')
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        if self.degree or self.branch:
            return f"{name} ({self.degree or self.branch})"
        return name

    def get_branch_display(self):
        branch_dict = dict(self.BRANCH_CHOICES)
        return branch_dict.get(self.branch, self.branch or 'Engineering')

    @property
    def display_phone(self):
        return self.phone or getattr(self.user, 'phone', '')

    @property
    def display_college(self):
        if self.college_name:
            return self.college_name
        if self.institution:
            return self.institution.name
        return ''

    @property
    def display_course(self):
        parts = []
        if self.degree:
            parts.append(self.degree)
        if self.branch:
            parts.append(f"in {self.branch}")
        return " ".join(parts)

    @property
    def completion_percentage(self):
        """Calculates dynamic profile completion percentage."""
        score = 15 # User account exists
        if self.profile_picture: score += 10
        if self.phone or getattr(self.user, 'phone', ''): score += 10
        if self.college_name or self.institution: score += 15
        if self.degree: score += 10
        if self.cgpa: score += 10
        if self.school_name or self.school_marks or self.tenth_marks or self.twelfth_marks: score += 10
        if self.resumes.exists(): score += 15
        if self.projects.exists(): score += 10
        if self.github_url or self.linkedin_url or self.portfolio_url: score += 5
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

