from django.contrib import admin
from .models import Assessment, AssessmentAttempt, DeviceTelemetry

@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'difficulty', 'duration_minutes', 'is_active')
    list_filter = ('category', 'difficulty', 'is_active')
    search_fields = ('title', 'description')

@admin.register(AssessmentAttempt)
class AssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'assessment', 'score', 'is_passed', 'started_at')
    list_filter = ('is_passed', 'assessment')
    search_fields = ('student__user__username', 'assessment__title')

@admin.register(DeviceTelemetry)
class DeviceTelemetryAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'input_modality', 'viewport_width', 'viewport_height', 'round_trip_latency_ms')

