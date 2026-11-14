from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import StudentProfile, Project, Resume, StudentSkill

@login_required
def dashboard(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    projects = profile.projects.all()
    skills = profile.skills.all()
    resumes = profile.resumes.all()
    
    return render(request, 'students/dashboard.html', {
        'profile': profile,
        'projects': projects,
        'skills': skills,
        'resumes': resumes,
        'title': 'Student Dashboard',
    })

def public_portfolio(request, student_id):
    profile = get_object_or_404(StudentProfile, id=student_id)
    projects = profile.projects.all()
    skills = profile.skills.all()
    return render(request, 'students/portfolio.html', {
        'profile': profile,
        'projects': projects,
        'skills': skills,
    })

