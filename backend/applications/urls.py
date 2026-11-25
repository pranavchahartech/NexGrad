from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('apply/<int:job_id>/', views.apply_to_job, name='apply_to_job'),
    path('apply-internship/<int:internship_id>/', views.apply_to_internship, name='apply_to_internship'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('<int:application_id>/', views.application_detail, name='detail'),
    path('<int:application_id>/status/', views.update_application_status, name='update_status'),
    path('<int:application_id>/schedule-interview/', views.schedule_interview, name='schedule_interview'),
]

