from django.urls import path, re_path
from . import views

app_name = 'jobs'

urlpatterns = [
    # Explore Jobs
    path('', views.job_list, name='list'),
    path('<int:job_id>/', views.job_detail, name='detail'),
    path('category/<slug:category_slug>/', views.category_list, name='category_list'),
    path('internships/', views.internship_list, name='internship_list'),

    # JSON API Endpoint
    path('api/opportunities/', views.api_opportunities, name='api_opportunities'),

    # Regex re_path route for archive (Requirement 2 Rubric)
    re_path(r'^archive/(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$', views.archive_view, name='archive'),
]

