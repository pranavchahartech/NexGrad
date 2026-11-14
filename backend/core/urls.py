from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('career-guidance/', views.career_guidance, name='career_guidance'),
    path('for-recruiters/', views.for_recruiters, name='for_recruiters'),
    path('for-institutions/', views.for_institutions, name='for_institutions'),
    path('developers/', views.api_docs, name='api_docs'),
]

