from django.urls import path
from . import views

app_name = 'assessments'

urlpatterns = [
    path('', views.assessment_list, name='list'),
    path('<int:assessment_id>/', views.assessment_detail, name='detail'),
    path('<int:assessment_id>/take/', views.take_assessment, name='take'),
    path('result/<int:attempt_id>/', views.assessment_result, name='result'),
]

