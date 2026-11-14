"""
Nexgrad URL Configuration
The Engineering Career Intelligence & Opportunity Platform.
"""

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from core import views as core_views

urlpatterns = [
    # Infrastructure Health Check
    path('health/', core_views.health_check, name='health_check'),

    # Admin Interface
    path('admin/', admin.site.urls),

    # Core Public Website
    path('', include('core.urls', namespace='core')),

    # Role-Based Authentication
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # Domain Applications
    path('jobs/', include('jobs.urls', namespace='jobs')),
    path('students/', include('students.urls', namespace='students')),
    path('recruiters/', include('recruiters.urls', namespace='recruiters')),
    path('institutions/', include('institutions.urls', namespace='institutions')),
    path('applications/', include('applications.urls', namespace='applications')),
    path('assessments/', include('assessments.urls', namespace='assessments')),
    path('notifications/', include('notifications.urls', namespace='notifications')),
    path('assistant/', include('ai_assistant.urls', namespace='ai_assistant')),
    path('', include('challenges.urls', namespace='challenges')),
]

# Development Media & Static Serving
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])

# Custom HTTP Error Handlers
handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'

