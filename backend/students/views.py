import os
import mimetypes
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404, HttpResponseForbidden, JsonResponse
from .models import StudentProfile, Project, Resume, StudentSkill
from .forms import StudentProfileForm, ProjectForm, SkillForm
from applications.models import Application
from challenges.models import ChallengeAssignment
from jobs.models import Job

@login_required
def dashboard(request):
    profile, _ = StudentProfile.objects.get_or_create(user=request.user)
    projects = profile.projects.all().order_by('-created_at')
    skills = profile.skills.all()
    resumes = profile.resumes.order_by('-uploaded_at')
    latest_resume = resumes.filter(is_default=True).first() or resumes.first()
    has_resume = latest_resume is not None

    # Check whether to show the big resume upload prompt banner:
    show_resume_prompt = (not has_resume) and (not request.session.get('skip_resume_prompt', False))
    is_new_user = request.session.pop('is_new_user', False) or request.session.pop('just_registered', False)

    # Job & Internship Applications
    applications_qs = Application.objects.filter(student=profile).select_related(
        'job', 'internship', 'job__company', 'internship__company'
    ).order_by('-applied_at')
    applications_count = applications_qs.count()
    recent_applications = applications_qs[:5]
    interview_count = applications_qs.filter(status__in=[Application.Status.INTERVIEW, Application.Status.SHORTLISTED]).count()

    # Recruiter Challenge Assignments
    challenges_qs = ChallengeAssignment.objects.filter(student=profile).select_related(
        'challenge', 'challenge__recruiter', 'challenge__recruiter__company'
    ).order_by('-assigned_at')
    challenges_count = challenges_qs.count()
    active_challenges = challenges_qs.filter(status__in=[ChallengeAssignment.Status.ASSIGNED, ChallengeAssignment.Status.IN_PROGRESS])[:4]
    pending_challenges_count = active_challenges.count()

    # Recommended Opportunities
    recommended_jobs = Job.objects.filter(is_active=True).select_related('company', 'recruiter').order_by('-created_at')[:3]

    # Dynamic Career Readiness Score (0-100)
    readiness_score = profile.completion_percentage
    if skills.count() >= 3:
        readiness_score = min(100, readiness_score + 5)
    if projects.count() >= 1:
        readiness_score = min(100, readiness_score + 5)
    if applications_count >= 1:
        readiness_score = min(100, readiness_score + 5)

    return render(request, 'students/dashboard.html', {
        'profile': profile,
        'projects': projects,
        'skills': skills,
        'resumes': resumes,
        'latest_resume': latest_resume,
        'has_resume': has_resume,
        'show_resume_prompt': show_resume_prompt,
        'is_new_user': is_new_user,
        'applications_count': applications_count,
        'recent_applications': recent_applications,
        'interview_count': interview_count,
        'challenges_count': challenges_count,
        'active_challenges': active_challenges,
        'pending_challenges_count': pending_challenges_count,
        'recommended_jobs': recommended_jobs,
        'career_readiness_score': readiness_score,
        'project_form': ProjectForm(),
        'skill_form': SkillForm(),
        'title': 'Student Workspace',
    })

@login_required
def edit_profile(request):
    """
    Allows a student to view and edit their full academic, contact, and personal profile:
    Photo, Phone, Address, College, Course, CGPA, School details, and Links.
    """
    if not getattr(request.user, 'is_student', False) and getattr(request.user, 'role', '') != 'STUDENT':
        messages.error(request, "Only students can access the student profile editor.")
        return redirect('core:home')

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            # Update user model fields
            request.user.first_name = form.cleaned_data.get('first_name', '').strip()
            request.user.last_name = form.cleaned_data.get('last_name', '').strip()
            phone = form.cleaned_data.get('phone', '').strip()
            if phone:
                request.user.phone = phone
            request.user.save()

            # Save student profile fields
            profile = form.save(commit=False)
            if phone:
                profile.phone = phone
            profile.save()

            messages.success(request, "Your profile details have been successfully saved!")
            return redirect('students:dashboard')
        else:
            messages.error(request, "Please check the form for errors.")
    else:
        form = StudentProfileForm(instance=profile, user=request.user)

    return render(request, 'students/edit_profile.html', {
        'form': form,
        'profile': profile,
        'title': 'Edit Profile — Nexgrad',
    })

@login_required
def upload_resume(request):
    """
    Handles uploading a new resume or updating an existing one.
    Saves file to media storage and metadata into the MySQL students_resume table.
    """
    if request.method != 'POST':
        return redirect('students:dashboard')

    if not getattr(request.user, 'is_student', False) and getattr(request.user, 'role', '') != 'STUDENT':
        messages.error(request, "Only registered students can upload resumes.")
        return redirect('core:home')

    profile, _ = StudentProfile.objects.get_or_create(user=request.user)

    resume_file = request.FILES.get('resume_file')
    if not resume_file:
        messages.error(request, "Please choose a resume file to upload.")
        return redirect(request.POST.get('next') or 'students:dashboard')

    # Validate file extension
    ext = os.path.splitext(resume_file.name)[1].lower()
    allowed_extensions = ['.pdf', '.doc', '.docx']
    if ext not in allowed_extensions:
        messages.error(request, f"Unsupported file format '{ext}'. Please upload a PDF, DOC, or DOCX document.")
        return redirect(request.POST.get('next') or 'students:dashboard')

    # Validate file size (10 MB maximum)
    if resume_file.size > 10 * 1024 * 1024:
        messages.error(request, "File size exceeds the 10MB limit. Please upload a smaller file.")
        return redirect(request.POST.get('next') or 'students:dashboard')

    title = request.POST.get('title', '').strip()
    if not title:
        raw_name = os.path.splitext(resume_file.name)[0].replace('_', ' ').replace('-', ' ').title()
        title = raw_name if raw_name else 'Primary Technical Resume'

    is_update = request.POST.get('is_update') == 'true' or profile.resumes.exists()

    # Unmark previous resumes as default
    profile.resumes.update(is_default=False)

    # Create new Resume record in the MySQL database
    new_resume = Resume.objects.create(
        student=profile,
        title=title,
        file=resume_file,
        is_default=True
    )

    # Clear skip flag in session since resume is now present
    request.session.pop('skip_resume_prompt', None)

    if is_update:
        messages.success(request, f"Resume successfully updated! '{new_resume.title}' is now your active CV.")
    else:
        messages.success(request, f"Resume uploaded successfully! '{new_resume.title}' is saved to your profile (+15% Profile Completion).")

    return redirect(request.POST.get('next') or 'students:dashboard')

@login_required
def skip_resume_prompt(request):
    """
    Saves the user's decision to skip/upload later in their session.
    """
    request.session['skip_resume_prompt'] = True
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'status': 'skipped', 'message': 'Resume prompt dismissed for this session.'})

    messages.info(request, "Resume upload skipped. You can upload your CV anytime from your workspace.")
    return redirect(request.GET.get('next') or 'students:dashboard')

@login_required
def view_resume(request, resume_id):
    """
    Streams the resume file inline so it can be previewed directly in the browser.
    Ensures secure access control (student owner, recruiter, or admin).
    """
    resume = get_object_or_404(Resume, id=resume_id)
    is_owner = (resume.student.user == request.user)
    is_recruiter = getattr(request.user, 'is_recruiter', False)
    is_staff = request.user.is_staff or getattr(request.user, 'role', '') == 'ADMIN'

    if not (is_owner or is_recruiter or is_staff):
        return HttpResponseForbidden("You do not have permission to view this resume.")

    if not resume.file:
        raise Http404("Resume file record does not have an attached file.")

    try:
        file_path = resume.file.path
        if not os.path.exists(file_path):
            raise Http404("Resume file could not be found on the server.")

        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or 'application/pdf'

        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'inline; filename="{os.path.basename(resume.file.name)}"'
        return response
    except Exception as e:
        # Fallback to direct URL if path retrieval fails
        return redirect(resume.file.url)

@login_required
def delete_resume(request, resume_id):
    """
    Allows a student to delete an uploaded resume version.
    """
    if request.method != 'POST':
        return redirect('students:dashboard')

    resume = get_object_or_404(Resume, id=resume_id, student__user=request.user)
    was_default = resume.is_default
    resume_title = resume.title

    # Delete the record (and file if needed)
    try:
        if resume.file and os.path.exists(resume.file.path):
            os.remove(resume.file.path)
    except Exception:
        pass

    resume.delete()

    # If it was default, make the next latest default
    if was_default:
        next_resume = Resume.objects.filter(student__user=request.user).order_by('-uploaded_at').first()
        if next_resume:
            next_resume.is_default = True
            next_resume.save()

    messages.info(request, f"Resume '{resume_title}' has been removed.")
    return redirect('students:dashboard')

def public_portfolio(request, student_id):
    profile = get_object_or_404(StudentProfile, id=student_id)
    projects = profile.projects.all()
    skills = profile.skills.all()
    return render(request, 'students/portfolio.html', {
        'profile': profile,
        'projects': projects,
        'skills': skills,
    })

@login_required
def add_project(request):
    """Adds a new engineering project from the Student Workspace."""
    if request.method == 'POST':
        profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.student = profile
            project.save()
            messages.success(request, f"Project '{project.title}' added successfully!")
        else:
            messages.error(request, "Failed to add project. Please verify the required fields.")
    return redirect('students:dashboard')

@login_required
def delete_project(request, project_id):
    """Deletes a student engineering project."""
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id, student__user=request.user)
        title = project.title
        project.delete()
        messages.info(request, f"Project '{title}' has been removed.")
    return redirect('students:dashboard')

@login_required
def add_skill(request):
    """Adds a new technical competency/skill from the Student Workspace."""
    if request.method == 'POST':
        profile, _ = StudentProfile.objects.get_or_create(user=request.user)
        form = SkillForm(request.POST)
        if form.is_valid():
            skill_name = form.cleaned_data['skill_name'].strip()
            # Prevent duplicate skill
            existing = StudentSkill.objects.filter(student=profile, skill_name__iexact=skill_name).first()
            if existing:
                existing.proficiency = form.cleaned_data['proficiency']
                existing.save()
                messages.info(request, f"Updated proficiency for '{skill_name}'.")
            else:
                skill = form.save(commit=False)
                skill.student = profile
                skill.save()
                messages.success(request, f"Skill '{skill.skill_name}' added successfully!")
        else:
            messages.error(request, "Please enter a valid skill name.")
    return redirect('students:dashboard')

@login_required
def delete_skill(request, skill_id):
    """Deletes a technical competency/skill."""
    if request.method == 'POST':
        skill = get_object_or_404(StudentSkill, id=skill_id, student__user=request.user)
        name = skill.skill_name
        skill.delete()
        messages.info(request, f"Skill '{name}' has been removed.")
    return redirect('students:dashboard')



