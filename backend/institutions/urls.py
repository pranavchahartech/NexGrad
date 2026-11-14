from django.urls import path
from . import views

app_name = 'institutions'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
]

