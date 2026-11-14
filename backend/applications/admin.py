from django.contrib import admin
from .models import Application, ApplicationStatusHistory, Interview

class StatusHistoryInline(admin.TabularInline):
    model = ApplicationStatusHistory
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'updated_by', 'timestamp', 'notes')

class InterviewInline(admin.StackedInline):
    model = Interview
    extra = 0

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'job', 'internship', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('student__user__username', 'job__title', 'internship__title')
    inlines = [StatusHistoryInline, InterviewInline]

@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ('application', 'round_name', 'scheduled_time', 'is_completed')
    list_filter = ('is_completed', 'scheduled_time')

