from django.urls import path
from . import views

app_name = 'career_intelligence'

urlpatterns = [
    path('roadmap/<str:target_role>/', views.roadmap_detail, name='roadmap_detail'),
]

