from django.db import models

class CareerRoadmap(models.Model):
    title = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True)
    target_role = models.CharField(max_length=100)
    summary = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Roadmap: {self.target_role}"

class RoadmapMilestone(models.Model):
    LEVEL_CHOICES = (
        ('FOUNDATIONAL', 'Foundational Competency'),
        ('INTERMEDIATE', 'Applied Engineering'),
        ('ADVANCED', 'Enterprise & Production Systems'),
    )
    roadmap = models.ForeignKey(CareerRoadmap, on_delete=models.CASCADE, related_name='milestones')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='FOUNDATIONAL')
    title = models.CharField(max_length=150)
    description = models.TextField()
    recommended_skills = models.CharField(max_length=250, help_text="Comma-separated skill names")
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.roadmap.target_role} - {self.title} ({self.get_level_display()})"

