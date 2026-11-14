from django.contrib import admin
from .models import CareerRoadmap, RoadmapMilestone

class RoadmapMilestoneInline(admin.TabularInline):
    model = RoadmapMilestone
    extra = 3

@admin.register(CareerRoadmap)
class CareerRoadmapAdmin(admin.ModelAdmin):
    list_display = ('target_role', 'title', 'is_active')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [RoadmapMilestoneInline]

