from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_verified', 'is_staff')
    list_filter = ('role', 'is_verified', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Nexgrad Roles & Verification', {'fields': ('role', 'phone', 'is_verified')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Nexgrad Roles & Verification', {'fields': ('role', 'phone', 'is_verified')}),
    )

