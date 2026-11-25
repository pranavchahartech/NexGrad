from django.urls import path
from . import views

app_name = 'recruiters'

urlpatterns = [
    # Recruiter Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('post-internship/', views.post_internship, name='post_internship'),
    path('post-job/', views.post_job, name='post_job'),
    
    # Company Profile & Public Listings
    path('company/<slug:company_slug>/', views.company_detail, name='company_detail'),
    path('company/<slug:company_slug>/dashboard/', views.company_recruiter_dashboard, name='company_recruiter_dashboard'),
    path('company/<slug:company_slug>/claim/', views.claim_company_account, name='claim_company_account'),

    # Administrator Discovery & Ingestion Control Center
    path('admin/discovery/', views.admin_discovery_dashboard, name='admin_discovery'),
    path('admin/import-board/', views.admin_trigger_import, name='admin_trigger_import'),
    path('admin/sync-board/<int:board_id>/', views.admin_sync_board, name='admin_sync_board'),
    path('admin/claim/<int:claim_id>/<str:decision>/', views.admin_decide_claim, name='admin_decide_claim'),
]
