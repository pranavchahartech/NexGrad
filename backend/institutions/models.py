from django.db import models
from django.conf import settings

class Institution(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    code = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=150, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Department(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, blank=True)

    class Meta:
        unique_together = ('institution', 'name')
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.institution.name})"

