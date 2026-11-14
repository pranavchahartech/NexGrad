from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('portfolio/<int:student_id>/', views.public_portfolio, name='public_portfolio'),
]

