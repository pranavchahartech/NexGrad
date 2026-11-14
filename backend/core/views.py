from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from accounts.models import CustomUser

def health_check(request):
    """
    Lightweight health check endpoint for Load Balancers, Nagios, and Ansible deployment verification.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'nexgrad-backend',
        'environment': 'production' if not settings.DEBUG else 'development'
    }, status=200)

def home(request):
    """
    Renders the official Nexgrad homepage matching the verified design specification.
    Populates dynamic statistics and featured engineering vacancies from the database.
    """
    # Safe queries for database-backed statistics with demo fallbacks if DB is empty
    student_count = CustomUser.objects.filter(role=CustomUser.Role.STUDENT).count()
    recruiter_count = CustomUser.objects.filter(role=CustomUser.Role.RECRUITER).count()

    # Try to fetch active jobs from jobs app if models exist
    try:
        from jobs.models import Job, Internship
        job_count = Job.objects.filter(is_active=True).count() + Internship.objects.filter(is_active=True).count()
        featured_jobs = Job.objects.filter(is_active=True).order_by('-created_at')[:6]
    except Exception:
        job_count = 0
        featured_jobs = []

    context = {
        'student_count': student_count if student_count > 0 else "10,000+",
        'recruiter_count': recruiter_count if recruiter_count > 0 else "500+",
        'job_count': job_count if job_count > 0 else "5,000+",
        'featured_jobs': featured_jobs,
        'active_page': 'home',
    }
    return render(request, 'core/home.html', context)

def about(request):
    return render(request, 'core/about.html', {'active_page': 'about'})

def career_guidance(request):
    return render(request, 'core/career_guidance.html', {'active_page': 'career_guidance'})

def for_recruiters(request):
    return render(request, 'core/for_recruiters.html', {'active_page': 'for_recruiters'})

def for_institutions(request):
    return render(request, 'core/for_institutions.html', {'active_page': 'for_institutions'})

def api_docs(request):
    return render(request, 'core/api_docs.html', {'active_page': 'developers'})

def custom_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def custom_500(request):
    return render(request, 'errors/500.html', status=500)

