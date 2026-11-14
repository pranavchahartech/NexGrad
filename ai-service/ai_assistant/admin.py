from django.contrib import admin
from .models import (
    AIConversation, ConversationState, AIMessage, StudentAIMemory, MemoryUpdateLog,
    StudentCareerGoal, StudentLearningPlan, LearningPlanProgress,
    InterviewSession, InterviewQuestion, ResumeAnalysis,
    AIMessageFeedback, AIUsageLog
)


class AIMessageInline(admin.TabularInline):
    model = AIMessage
    extra = 0
    readonly_fields = ('created_at', 'tokens_used')
    fields = ('role', 'content', 'tokens_used', 'created_at')


class ConversationStateInline(admin.StackedInline):
    model = ConversationState
    extra = 0
    readonly_fields = ('updated_at',)


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'is_pinned', 'created_at', 'updated_at')
    list_filter = ('is_pinned', 'is_archived', 'created_at')
    search_fields = ('title', 'student__user__username', 'student__user__first_name', 'student__user__last_name')
    inlines = [ConversationStateInline, AIMessageInline]


@admin.register(ConversationState)
class ConversationStateAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'active_intent', 'active_task', 'active_entity_type', 'updated_at')
    search_fields = ('conversation__title', 'active_intent', 'active_task')



@admin.register(StudentAIMemory)
class StudentAIMemoryAdmin(admin.ModelAdmin):
    list_display = ('student', 'category', 'key', 'is_active', 'confidence', 'updated_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('key', 'value', 'student__user__username')


@admin.register(StudentLearningPlan)
class StudentLearningPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'target_role', 'duration_weeks', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'target_role', 'student__user__username')


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('student', 'target_role', 'interview_type', 'status', 'created_at')
    list_filter = ('interview_type', 'status', 'created_at')
    search_fields = ('target_role', 'student__user__username')


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = ('student', 'target_role', 'created_at')
    search_fields = ('target_role', 'student__user__username')


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'model_name', 'action_type', 'prompt_tokens', 'candidate_tokens', 'timestamp')
    list_filter = ('model_name', 'action_type', 'timestamp')

