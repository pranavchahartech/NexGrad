from django.contrib import admin
from .models import StudentProfile, Resume, Project, StudentSkill

class ResumeInline(admin.TabularInline):
    model = Resume
    extra = 1

class ProjectInline(admin.StackedInline):
    model = Project
    extra = 1

class StudentSkillInline(admin.TabularInline):
    model = StudentSkill
    extra = 2

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'branch', 'graduation_year', 'cgpa', 'institution')
    list_filter = ('branch', 'graduation_year', 'institution')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    inlines = [ResumeInline, ProjectInline, StudentSkillInline]

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'technologies', 'created_at')
    search_fields = ('title', 'technologies', 'student__user__username')

