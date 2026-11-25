from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Application, ApplicationStatusHistory, Interview
from jobs.models import Job, Internship
from students.models import StudentProfile


def can_manage_application(user, application):
    """
    Check if the user has authorization to review or update this candidate application.
    Authorized users: Platform Staff/Admin or the Recruiter assigned to the target company.
    """
    if user.is_staff or getattr(user, 'role', '') == 'ADMIN':
        return True
    if user.is_recruiter and hasattr(user, 'recruiter_profile'):
        rec_company = user.recruiter_profile.company
        app_company = application.job.company if application.job else (application.internship.company if application.internship else None)
        return rec_company is not None and rec_company == app_company
    return False


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
        resume_id = request.POST.get('resume_id')
        if resume_id:
            chosen_resume = student_profile.resumes.filter(id=resume_id).first()
        else:
            chosen_resume = student_profile.resumes.filter(is_default=True).first() or student_profile.resumes.first()

        app = Application.objects.create(
            student=student_profile,
            job=job,
            internship=None,
            resume=chosen_resume,
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

    resumes = student_profile.resumes.all()
    default_resume = student_profile.resumes.filter(is_default=True).first() or resumes.first()

    return render(request, 'applications/apply.html', {
        'job': job,
        'profile': student_profile,
        'resumes': resumes,
        'default_resume': default_resume,
    })


@login_required
def apply_to_internship(request, internship_id):
    """
    Submits an engineering internship application with duplicate prevention,
    CV linkage, and automatic candidate pipeline registration.
    """
    if not request.user.is_student:
        messages.error(request, "Only registered engineering students can apply for internship opportunities.")
        return redirect('jobs:internship_detail', internship_id=internship_id)

    internship = get_object_or_404(Internship, id=internship_id)
    student_profile = get_object_or_404(StudentProfile, user=request.user)

    # Check duplicate application
    if Application.objects.filter(student=student_profile, internship=internship).exists():
        messages.warning(request, "You have already applied for this internship position.")
        return redirect('jobs:internship_detail', internship_id=internship_id)

    if request.method == 'POST':
        cover_letter = request.POST.get('cover_letter', '').strip()
        resume_id = request.POST.get('resume_id')
        if resume_id:
            chosen_resume = student_profile.resumes.filter(id=resume_id).first()
        else:
            chosen_resume = student_profile.resumes.filter(is_default=True).first() or student_profile.resumes.first()

        app = Application.objects.create(
            student=student_profile,
            internship=internship,
            job=None,
            resume=chosen_resume,
            cover_letter=cover_letter,
            status=Application.Status.APPLIED
        )

        ApplicationStatusHistory.objects.create(
            application=app,
            from_status='DRAFT',
            to_status=Application.Status.APPLIED,
            updated_by=request.user,
            notes='Candidate submitted engineering internship application via Nexgrad portal.'
        )

        messages.success(request, f"Internship application successfully submitted for {internship.title} at {internship.company.name}!")
        return redirect('applications:my_applications')

    resumes = student_profile.resumes.all()
    default_resume = student_profile.resumes.filter(is_default=True).first() or resumes.first()

    return render(request, 'applications/apply_internship.html', {
        'internship': internship,
        'profile': student_profile,
        'resumes': resumes,
        'default_resume': default_resume,
    })


@login_required
def my_applications(request):
    """
    Candidate application tracking board showing both Full-Time Jobs and Internships.
    """
    if not hasattr(request.user, 'student_profile') or not request.user.is_student:
        messages.info(request, "Application tracking is designed for candidate engineering students.")
        return redirect('core:home')

    student_profile = request.user.student_profile
    applications = Application.objects.filter(student=student_profile).select_related(
        'job', 'internship', 'job__company', 'internship__company', 'resume'
    )
    return render(request, 'applications/my_applications.html', {
        'applications': applications,
        'title': 'My Applications Tracker'
    })


@login_required
def application_detail(request, application_id):
    """
    Application inspection detail view for both Candidates and Recruiters.
    Includes stage pipeline, audit logs, recruiter evaluation tools, and interview scheduler.
    """
    application = get_object_or_404(
        Application.objects.select_related('student__user', 'student__institution', 'job__company', 'internship__company', 'resume'),
        id=application_id
    )

    is_manager = can_manage_application(request.user, application)
    is_candidate = (request.user == application.student.user)

    if not is_candidate and not is_manager:
        messages.error(request, "Unauthorized access to candidate application record.")
        return redirect('core:home')

    history = application.status_history.all()
    interviews = application.interviews.all()
    status_choices = Application.Status.choices

    return render(request, 'applications/detail.html', {
        'application': application,
        'history': history,
        'interviews': interviews,
        'is_manager': is_manager,
        'is_candidate': is_candidate,
        'status_choices': status_choices,
    })


@login_required
def update_application_status(request, application_id):
    """
    Recruiter action: Advance or modify application stage, recording audit notes.
    """
    application = get_object_or_404(Application, id=application_id)

    if not can_manage_application(request.user, application):
        messages.error(request, "You do not have permission to manage this application.")
        return redirect('applications:detail', application_id=application_id)

    if request.method == 'POST':
        new_status = request.POST.get('status', '').strip()
        notes = request.POST.get('notes', '').strip()

        if new_status in Application.Status.values and new_status != application.status:
            old_status = application.status
            application.status = new_status
            application.save()

            ApplicationStatusHistory.objects.create(
                application=application,
                from_status=old_status,
                to_status=new_status,
                updated_by=request.user,
                notes=notes or f"Recruiter transitioned candidate to {application.get_status_display()}."
            )
            messages.success(request, f"Application #{application.id} status updated to {application.get_status_display()}.")
        else:
            messages.info(request, "No status change was made.")

    return redirect('applications:detail', application_id=application_id)


@login_required
def schedule_interview(request, application_id):
    """
    Recruiter action: Schedule an interview round with meeting link and candidate instructions.
    """
    application = get_object_or_404(Application, id=application_id)

    if not can_manage_application(request.user, application):
        messages.error(request, "You do not have permission to schedule interviews for this application.")
        return redirect('applications:detail', application_id=application_id)

    if request.method == 'POST':
        round_name = request.POST.get('round_name', 'Technical Interview Round').strip()
        scheduled_time_str = request.POST.get('scheduled_time', '').strip()
        meeting_link = request.POST.get('meeting_link', 'https://meet.google.com/nex-grad-room').strip()
        interviewer = request.POST.get('interviewer', 'Technical Talent Lead').strip()
        instructions = request.POST.get('instructions', '').strip()

        if not scheduled_time_str:
            messages.error(request, "Please specify a valid interview date and time.")
            return redirect('applications:detail', application_id=application_id)

        try:
            # Parse datetime-local format
            scheduled_time = timezone.datetime.fromisoformat(scheduled_time_str)
            if timezone.is_naive(scheduled_time):
                scheduled_time = timezone.make_aware(scheduled_time)
        except Exception:
            messages.error(request, "Invalid date/time format provided.")
            return redirect('applications:detail', application_id=application_id)

        interview = Interview.objects.create(
            application=application,
            round_name=round_name,
            scheduled_time=scheduled_time,
            meeting_link=meeting_link,
            interviewer=interviewer,
            instructions=instructions,
        )

        # Transition application to INTERVIEW if not already there
        if application.status != Application.Status.INTERVIEW:
            old_status = application.status
            application.status = Application.Status.INTERVIEW
            application.save()

            ApplicationStatusHistory.objects.create(
                application=application,
                from_status=old_status,
                to_status=Application.Status.INTERVIEW,
                updated_by=request.user,
                notes=f"Interview scheduled: {round_name} on {scheduled_time.strftime('%b %d, %Y at %I:%M %p')} with {interviewer}."
            )

        messages.success(request, f"Interview round '{round_name}' successfully scheduled for candidate {application.student.user.get_full_name()}!")

    return redirect('applications:detail', application_id=application_id)
