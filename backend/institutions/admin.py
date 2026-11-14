from django.contrib import admin
from .models import Institution, Department

@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'location', 'is_verified', 'created_at')
    search_fields = ('name', 'code', 'location')
    list_filter = ('is_verified',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'institution')
    list_filter = ('institution',)
    search_fields = ('name', 'code')

