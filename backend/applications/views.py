from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Application, ApplicationStatusHistory
from jobs.models import Job
from students.models import StudentProfile

@login_required
def apply_to_job(request, job_id):
    """
    Submits a job application with duplicate prevention and history logging.
    """
    if not request.user.is_student:
        messages.error(request, "Only registered engineering students can apply for vacancies.")
        return redirect('jobs:detail', job_id=job_id)

    job = get_object_or_404(Job, id=job_id)
    student_profile = get_object_or_404(StudentProfile, user=request.user)

    # Check if application already exists
    if Application.objects.filter(student=student_profile, job=job).exists():
        messages.warning(request, "You have already applied for this opportunity.")
        return redirect('jobs:detail', job_id=job_id)

    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '').strip()
        default_resume = student_profile.resumes.filter(is_default=True).first()

        app = Application.objects.create(
            student=student_profile,
            job=job,
            resume=default_resume,
            cover_letter=cover_letter,
            status=Application.Status.APPLIED
        )

        ApplicationStatusHistory.objects.create(
            application=app,
            from_status='DRAFT',
            to_status=Application.Status.APPLIED,
            updated_by=request.user,
            notes='Initial candidate application submitted via portal.'
        )

        messages.success(request, f"Application successfully submitted for {job.title} at {job.company.name}!")
        return redirect('applications:my_applications')

    return render(request, 'applications/apply.html', {'job': job, 'profile': student_profile})

@login_required
def my_applications(request):
    """
    Candidate application tracking board.
    """
    if not hasattr(request.user, 'student_profile') or not request.user.is_student:
        messages.info(request, "Application tracking is designed for candidate engineering students.")
        return redirect('core:home')

    student_profile = request.user.student_profile
    applications = Application.objects.filter(student=student_profile).select_related('job', 'internship', 'job__company')
    return render(request, 'applications/my_applications.html', {
        'applications': applications,
        'title': 'My Applications Tracker'
    })

@login_required
def application_detail(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    # Ensure privacy: only candidate, assigned recruiter, or admin can inspect
    if request.user != application.student.user and not request.user.is_recruiter and not request.user.is_staff:
        messages.error(request, "Unauthorized access to candidate application record.")
        return redirect('core:home')

    history = application.status_history.all()
    interviews = application.interviews.all()
    return render(request, 'applications/detail.html', {
        'application': application,
        'history': history,
        'interviews': interviews,
    })

