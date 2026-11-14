from django.contrib import admin
from .models import Skill, Job, Internship, ExternalListing


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug')
    list_filter = ('category',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'job_type', 'is_external_import', 'external_source', 'location', 'is_active', 'created_at')
    list_filter = ('is_external_import', 'job_type', 'workplace_type', 'is_active', 'company')
    search_fields = ('title', 'company__name', 'external_id', 'description')
    filter_horizontal = ('required_skills',)


@admin.register(Internship)
class InternshipAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'is_external_import', 'external_source', 'duration', 'stipend', 'is_active')
    list_filter = ('is_external_import', 'is_active', 'company')
    search_fields = ('title', 'company__name', 'external_id')
    filter_horizontal = ('required_skills',)


@admin.register(ExternalListing)
class ExternalListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'source_provider', 'external_id', 'is_internship', 'is_active', 'last_synced_at')
    list_filter = ('source_provider', 'is_internship', 'is_active')
    search_fields = ('title', 'company__name', 'external_id')
