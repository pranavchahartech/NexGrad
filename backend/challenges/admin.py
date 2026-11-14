from django.contrib import admin
from .models import (
    Challenge, ChallengeAttachment, ChallengeAssignment,
    ChallengeSubmission, ChallengeEvaluation, ChallengeEvent
)

class ChallengeAttachmentInline(admin.TabularInline):
    model = ChallengeAttachment
    extra = 1

class ChallengeAssignmentInline(admin.TabularInline):
    model = ChallengeAssignment
    extra = 0
    readonly_fields = ('assigned_at', 'started_at', 'revoked_at')

@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'recruiter', 'job', 'challenge_type', 'difficulty', 'maximum_marks', 'deadline', 'status')
    list_filter = ('status', 'challenge_type', 'difficulty')
    search_fields = ('title', 'description', 'recruiter__user__username', 'recruiter__company__name')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ChallengeAttachmentInline, ChallengeAssignmentInline]

@admin.register(ChallengeAssignment)
class ChallengeAssignmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'challenge', 'status', 'assigned_at', 'deadline', 'assigned_by')
    list_filter = ('status', 'assigned_at')
    search_fields = ('student__user__username', 'challenge__title')
    readonly_fields = ('assigned_at', 'started_at', 'revoked_at')

@admin.register(ChallengeSubmission)
class ChallengeSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'submission_number', 'submitted_at', 'status')
    list_filter = ('status', 'submitted_at')
    search_fields = ('assignment__student__user__username', 'assignment__challenge__title')

@admin.register(ChallengeEvaluation)
class ChallengeEvaluationAdmin(admin.ModelAdmin):
    list_display = ('submission', 'evaluator', 'total_marks', 'recommended_stage', 'evaluation_status', 'evaluated_at')
    list_filter = ('evaluation_status', 'recommended_stage')
    search_fields = ('submission__assignment__student__user__username', 'evaluator__username')

@admin.register(ChallengeEvent)
class ChallengeEventAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'event_type', 'actor', 'created_at')
    list_filter = ('event_type', 'created_at')
    readonly_fields = ('created_at',)

