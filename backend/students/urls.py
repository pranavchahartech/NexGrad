from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('portfolio/<int:student_id>/', views.public_portfolio, name='public_portfolio'),
    path('resume/upload/', views.upload_resume, name='upload_resume'),
    path('resume/skip/', views.skip_resume_prompt, name='skip_resume_prompt'),
    path('resume/<int:resume_id>/view/', views.view_resume, name='view_resume'),
    path('resume/<int:resume_id>/delete/', views.delete_resume, name='delete_resume'),
    path('project/add/', views.add_project, name='add_project'),
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('skill/add/', views.add_skill, name='add_skill'),
    path('skill/<int:skill_id>/delete/', views.delete_skill, name='delete_skill'),
]


