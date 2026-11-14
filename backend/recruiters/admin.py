from django.contrib import admin
from .models import Company, CompanyBoard, RecruiterProfile, CompanyVerification, DataImportLog


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_provider', 'source_board_token', 'is_auto_generated', 'is_verified', 'created_at')
    list_filter = ('source_provider', 'is_auto_generated', 'is_verified', 'industry')
    search_fields = ('name', 'industry', 'headquarters', 'source_board_token')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CompanyBoard)
class CompanyBoardAdmin(admin.ModelAdmin):
    list_display = ('company', 'provider', 'board_token', 'sync_status', 'last_synced_at', 'is_active')
    list_filter = ('provider', 'sync_status', 'is_active')
    search_fields = ('company__name', 'board_token')


@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'internal_identifier', 'verification_status', 'is_auto_generated', 'is_verified')
    list_filter = ('verification_status', 'is_auto_generated', 'is_verified', 'company')
    search_fields = ('user__username', 'user__email', 'company__name', 'internal_identifier')


@admin.register(CompanyVerification)
class CompanyVerificationAdmin(admin.ModelAdmin):
    list_display = ('company', 'work_email', 'official_designation', 'claimant_user', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('company__name', 'work_email', 'claimant_user__username', 'official_designation')


@admin.register(DataImportLog)
class DataImportLogAdmin(admin.ModelAdmin):
    list_display = ('started_at', 'provider', 'board_token', 'company', 'status', 'jobs_discovered', 'jobs_created', 'jobs_deactivated')
    list_filter = ('status', 'provider', 'started_at')
    search_fields = ('board_token', 'company__name')
