from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Custom user model for Nexgrad with role-based access control.
    Supports Students, Recruiters, Institutions, and Admins.
    """
    class Role(models.TextChoices):
        STUDENT = 'STUDENT', 'Engineering Student'
        RECRUITER = 'RECRUITER', 'Company Recruiter'
        INSTITUTION = 'INSTITUTION', 'University / Placement Officer'
        ADMIN = 'ADMIN', 'Platform Administrator'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text="Designated role within the Nexgrad ecosystem."
    )
    email = models.EmailField(
        unique=True,
        help_text="Primary email address used for login and notifications."
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text="Contact telephone number."
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Administrative or institutional verification badge."
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_recruiter(self):
        return self.role == self.Role.RECRUITER

    @property
    def is_institution(self):
        return self.role == self.Role.INSTITUTION

