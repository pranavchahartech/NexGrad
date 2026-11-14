from django.urls import path
from . import views

app_name = 'applications'

urlpatterns = [
    path('apply/<int:job_id>/', views.apply_to_job, name='apply_to_job'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('<int:application_id>/', views.application_detail, name='detail'),
]

