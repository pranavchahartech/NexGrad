from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from .models import Company, CompanyBoard, RecruiterProfile, CompanyVerification, DataImportLog
from applications.models import Application, Interview
from challenges.models import Challenge
from jobs.models import Job, Internship


@login_required
def dashboard(request):
    """
    Recruiter Workspace & Pipeline:
    Shows live vacancy metrics, applicant tracking, and private challenge pipeline.
    Accessible only to registered recruiters.
    """
    if request.user.is_staff or getattr(request.user, 'role', '') == 'ADMIN':
        return redirect('recruiters:admin_discovery')

    profile = getattr(request.user, 'recruiter_profile', None)
    if not profile:
        messages.error(request, "Access restricted to registered recruiters.")
        return redirect('core:home')

    return _render_recruiter_dashboard(request, profile)


@login_required
def company_recruiter_dashboard(request, company_slug):
    """
    Company-specific recruiter dashboard for any imported or registered company.
    Accessible only to authorized recruiters representing this specific company.
    """
    company = get_object_or_404(Company, slug=company_slug)

    if request.user.is_staff or getattr(request.user, 'role', '') == 'ADMIN':
        messages.info(request, f"Admins manage company listings and ingestion through the Company Discovery & Ingestion Engine.")
        return redirect('recruiters:admin_discovery')

    profile = getattr(request.user, 'recruiter_profile', None)
    if not profile or profile.company != company:
        messages.error(request, f"Access restricted. You are not authorized to access {company.name}'s recruiter workspace.")
        return redirect('recruiters:company_detail', company_slug=company.slug)

    return _render_recruiter_dashboard(request, profile, company_context=company)


def _render_recruiter_dashboard(request, profile, company_context=None):
    company = company_context or (profile.company if profile else None)

    if profile:
        jobs = profile.posted_jobs.all()
        internships = profile.posted_internships.all()
        
        # Breakdown of listings (Requirement 4)
        total_jobs_count = jobs.count()
        total_internships_count = internships.count()
        active_jobs_count = jobs.filter(is_active=True).count()
        expired_jobs_count = jobs.filter(is_active=False).count()
        active_internships_count = internships.filter(is_active=True).count()
        
        external_jobs_count = jobs.filter(is_external_import=True).count()
        manual_jobs_count = jobs.filter(is_external_import=False).count()

        applications_qs = Application.objects.filter(
            Q(job__in=jobs) | Q(internship__in=internships)
        ).select_related(
            'student', 'student__user', 'student__institution', 'job', 'internship', 'resume'
        ).order_by('-applied_at')
        
        applications = applications_qs[:30]
        applications_count = applications_qs.count()
        interviews_count = Interview.objects.filter(
            Q(application__job__in=jobs) | Q(application__internship__in=internships),
            is_completed=False
        ).count()
        challenges = Challenge.objects.filter(recruiter=profile).select_related('job')
        challenges_count = challenges.count()
        
        board = company.primary_board if company else None
        claims = company.verification_claims.all() if company else []
    else:
        jobs = []
        internships = []
        total_jobs_count = 0
        total_internships_count = 0
        active_jobs_count = 0
        expired_jobs_count = 0
        active_internships_count = 0
        external_jobs_count = 0
        manual_jobs_count = 0
        applications = []
        applications_count = 0
        interviews_count = 0
        challenges = []
        challenges_count = 0
        board = None
        claims = []

    return render(request, 'recruiters/dashboard.html', {
        'title': f"{company.name if company else 'Recruiter'} Workspace & Pipeline",
        'profile': profile,
        'company': company,
        'jobs': jobs,
        'internships': internships,
        'applications': applications,
        'challenges': challenges,
        'total_jobs_count': total_jobs_count,
        'total_internships_count': total_internships_count,
        'active_jobs_count': active_jobs_count,
        'expired_jobs_count': expired_jobs_count,
        'active_internships_count': active_internships_count,
        'external_jobs_count': external_jobs_count,
        'manual_jobs_count': manual_jobs_count,
        'applications_count': applications_count,
        'interviews_count': interviews_count,
        'challenges_count': challenges_count,
        'board': board,
        'claims': claims,
    })


def company_detail(request, company_slug):
    """
    Public company profile displaying corporate information, active vacancies,
    internships, and official verification badges.
    """
    company = get_object_or_404(Company, slug=company_slug)
    jobs = company.jobs.filter(is_active=True)
    internships = company.internships.filter(is_active=True)
    board = company.primary_board
    recruiter_profile = company.recruiters.first()
    
    # Check if current user has an active claim
    user_claim = None
    if request.user.is_authenticated:
        user_claim = company.verification_claims.filter(claimant_user=request.user).first()

    return render(request, 'recruiters/company_detail.html', {
        'company': company,
        'jobs': jobs,
        'internships': internships,
        'board': board,
        'recruiter_profile': recruiter_profile,
        'user_claim': user_claim,
    })


@login_required
def claim_company_account(request, company_slug):
    """
    Official claim submission interface for company representatives to establish
    authorized ownership of auto-generated recruiter profiles.
    """
    if request.user.is_staff or getattr(request.user, 'role', '') == 'ADMIN':
        messages.info(request, "Administrators manage and approve company claims in the Discovery Control Center.")
        return redirect('recruiters:admin_discovery')

    company = get_object_or_404(Company, slug=company_slug)
    profile = company.recruiters.first()

    if not profile or not profile.is_auto_generated:
        messages.info(request, f"{company.name} is already managed by an authorized recruiter.")
        return redirect('recruiters:company_detail', company_slug=company.slug)

    # Check if already verified/claimed
    if profile.verification_status == RecruiterProfile.VerificationStatus.CLAIMED:
        messages.info(request, f"{company.name} has already been claimed and verified.")
        return redirect('recruiters:company_detail', company_slug=company.slug)

    # Check existing pending claim by this user
    existing_claim = CompanyVerification.objects.filter(
        company=company,
        claimant_user=request.user,
        status=CompanyVerification.Status.PENDING
    ).first()

    if request.method == 'POST':
        work_email = request.POST.get('work_email', '').strip()
        official_designation = request.POST.get('official_designation', '').strip()
        claim_statement = request.POST.get('claim_statement', '').strip()
        proof_link = request.POST.get('proof_link', '').strip()

        if not work_email or not official_designation or not claim_statement:
            messages.error(request, "Please fill in all required verification fields.")
        else:
            claim = CompanyVerification.objects.create(
                company=company,
                recruiter_profile=profile,
                claimant_user=request.user,
                work_email=work_email,
                official_designation=official_designation,
                claim_statement=claim_statement,
                proof_link=proof_link,
                status=CompanyVerification.Status.PENDING
            )
            # Update recruiter profile status
            profile.verification_status = RecruiterProfile.VerificationStatus.PENDING_REVIEW
            profile.save()

            messages.success(
                request,
                f"Your claim for {company.name} has been submitted! An administrator will review your corporate email and credentials shortly."
            )
            return redirect('recruiters:company_detail', company_slug=company.slug)

    return render(request, 'recruiters/claim_company.html', {
        'company': company,
        'profile': profile,
        'existing_claim': existing_claim,
    })


# ==============================================================================
# ADMINISTRATOR CONTROLS (Requirement 7)
# ==============================================================================

def _check_admin_access(request):
    if not (request.user.is_authenticated and (request.user.is_staff or getattr(request.user, 'role', '') == 'ADMIN')):
        raise PermissionDenied("Administrator privileges are required to access the Company Discovery Control Center.")


@login_required
def admin_discovery_dashboard(request):
    """
    Administrator Dashboard for managing automated company discovery,
    Greenhouse board ingestion, recruiter accounts, and verification claims.
    """
    _check_admin_access(request)

    companies = Company.objects.all().prefetch_related('recruiters', 'boards', 'jobs', 'internships')
    auto_companies = companies.filter(is_auto_generated=True)
    recruiter_profiles = RecruiterProfile.objects.filter(is_auto_generated=True).select_related('company', 'user')
    
    pending_claims = CompanyVerification.objects.filter(
        status=CompanyVerification.Status.PENDING
    ).select_related('company', 'recruiter_profile', 'claimant_user')
    
    decided_claims = CompanyVerification.objects.exclude(
        status=CompanyVerification.Status.PENDING
    ).select_related('company', 'recruiter_profile', 'claimant_user', 'reviewed_by')[:10]

    # Metrics
    total_companies = companies.count()
    auto_companies_count = auto_companies.count()
    total_auto_recruiters = recruiter_profiles.count()
    total_imported_jobs = Job.objects.filter(is_external_import=True).count()
    total_imported_internships = Internship.objects.filter(is_external_import=True).count()
    pending_claims_count = pending_claims.count()

    return render(request, 'recruiters/admin/discovery.html', {
        'companies': companies,
        'auto_companies': auto_companies,
        'recruiter_profiles': recruiter_profiles,
        'pending_claims': pending_claims,
        'decided_claims': decided_claims,
        'total_companies': total_companies,
        'auto_companies_count': auto_companies_count,
        'total_auto_recruiters': total_auto_recruiters,
        'total_imported_jobs': total_imported_jobs,
        'total_imported_internships': total_imported_internships,
        'pending_claims_count': pending_claims_count,
    })


@login_required
def admin_trigger_import(request):
    """
    Admin action: External Greenhouse API live ingestion has been retired.
    Registers or retrieves company records using offline database fixtures without network API calls.
    """
    _check_admin_access(request)

    if request.method == 'POST':
        board_token = request.POST.get('board_token', '').strip().lower()
        custom_name = request.POST.get('custom_name', '').strip() or None

        if not board_token:
            messages.error(request, "Please provide a valid company identifier.")
            return redirect('recruiters:admin_discovery')

        try:
            from .services.greenhouse_importer import GreenhouseJobBoardImporter
            importer = GreenhouseJobBoardImporter()
            res = importer.import_board(board_token, custom_name=custom_name)
            messages.success(
                request,
                f"Company {res['company'].name} confirmed in database catalog! "
                f"Recruiter Account: '{res['recruiter_user'].username}' (ID: {res['recruiter_profile'].internal_identifier})."
            )
        except Exception as e:
            messages.error(request, f"Error processing company record '{board_token}': {e}")

    return redirect('recruiters:admin_discovery')


@login_required
def admin_sync_board(request, board_id):
    """
    Admin action: External Greenhouse API re-synchronization has been retired.
    """
    _check_admin_access(request)
    board = get_object_or_404(CompanyBoard, id=board_id)
    messages.info(
        request,
        f"External API synchronization is disabled. All vacancies and company details for {board.company.name} remain preserved."
    )
    return redirect('recruiters:admin_discovery')


@login_required
def admin_decide_claim(request, claim_id, decision):
    """
    Admin action to approve or reject a company verification claim.
    """
    _check_admin_access(request)
    claim = get_object_or_404(CompanyVerification, id=claim_id)

    if request.method == 'POST':
        admin_notes = request.POST.get('admin_notes', '').strip()
        decision_lower = decision.lower()

        if decision_lower == 'approve':
            claim.status = CompanyVerification.Status.APPROVED
            claim.reviewed_by = request.user
            claim.reviewed_at = timezone.now()
            claim.admin_notes = admin_notes or "Verification approved. Corporate representative ownership confirmed."
            claim.save()

            # Transfer / Upgrade profile ownership
            profile = claim.recruiter_profile
            profile.verification_status = RecruiterProfile.VerificationStatus.CLAIMED
            profile.is_verified = True
            profile.claimed_by = claim.claimant_user
            profile.claimed_at = timezone.now()
            profile.save()

            # Mark company verified
            company = claim.company
            company.is_verified = True
            company.save()

            messages.success(
                request,
                f"Verification claim APPROVED for {company.name}! Recruiter management transferred to {claim.claimant_user.username} ({claim.work_email})."
            )
        elif decision_lower == 'reject':
            claim.status = CompanyVerification.Status.REJECTED
            claim.reviewed_by = request.user
            claim.reviewed_at = timezone.now()
            claim.admin_notes = admin_notes or "Verification rejected due to insufficient or unverified domain proof."
            claim.save()

            # Revert profile status
            profile = claim.recruiter_profile
            profile.verification_status = RecruiterProfile.VerificationStatus.UNVERIFIED
            profile.save()

            messages.warning(
                request,
                f"Verification claim for {claim.company.name} was REJECTED."
            )
        else:
            messages.error(request, f"Unknown decision '{decision}'.")

    return redirect('recruiters:admin_discovery')


@login_required
def post_internship(request):
    """
    Allows a verified recruiter to publish an engineering internship opportunity.
    Immediately reflects on the global internship explore board and student workspace.
    """
    profile = getattr(request.user, 'recruiter_profile', None)
    if not profile or not profile.company:
        messages.error(request, "Only registered recruiters associated with an official company can publish internships.")
        return redirect('recruiters:dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        duration = request.POST.get('duration', '6 Months').strip()
        stipend = request.POST.get('stipend', '₹50,000 / Month').strip()
        location = request.POST.get('location', 'Hybrid / Remote').strip()
        eligible_branches = request.POST.get('eligible_branches', 'CSE, ECE, IT').strip()
        description = request.POST.get('description', '').strip()
        deadline_str = request.POST.get('deadline', '').strip()
        skill_ids = request.POST.getlist('skills')

        if not title or not description:
            messages.error(request, "Please provide an internship title and detailed role description.")
            return redirect('recruiters:post_internship')

        deadline = None
        if deadline_str:
            try:
                deadline = timezone.datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                deadline = None

        internship = Internship.objects.create(
            company=profile.company,
            recruiter=profile,
            title=title,
            duration=duration,
            stipend=stipend,
            location=location,
            eligible_branches=eligible_branches,
            description=description,
            deadline=deadline,
            is_active=True
        )

        if skill_ids:
            internship.required_skills.set(skill_ids)

        messages.success(request, f"Internship '{internship.title}' has been successfully published!")
        return redirect('recruiters:dashboard')

    from jobs.models import Skill
    skills = Skill.objects.all()
    return render(request, 'recruiters/post_internship.html', {
        'profile': profile,
        'company': profile.company,
        'skills': skills,
    })


@login_required
def post_job(request):
    """
    Allows a verified recruiter to publish a full-time engineering vacancy.
    """
    profile = getattr(request.user, 'recruiter_profile', None)
    if not profile or not profile.company:
        messages.error(request, "Only registered recruiters associated with an official company can publish jobs.")
        return redirect('recruiters:dashboard')

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        job_type = request.POST.get('job_type', 'FULL_TIME')
        workplace_type = request.POST.get('workplace_type', 'HYBRID')
        location = request.POST.get('location', 'Bengaluru, India').strip()
        salary_range = request.POST.get('salary_range', '₹10,00,000 - ₹18,00,000 P.A.').strip()
        eligible_branches = request.POST.get('eligible_branches', 'CSE, ECE, IT').strip()
        min_cgpa = request.POST.get('min_cgpa', '7.00')
        description = request.POST.get('description', '').strip()
        responsibilities = request.POST.get('responsibilities', '').strip()
        requirements = request.POST.get('requirements', '').strip()
        deadline_str = request.POST.get('deadline', '').strip()
        skill_ids = request.POST.getlist('skills')

        if not title or not description:
            messages.error(request, "Please provide a job title and description.")
            return redirect('recruiters:post_job')

        try:
            min_cgpa_dec = float(min_cgpa)
        except ValueError:
            min_cgpa_dec = 7.00

        deadline = None
        if deadline_str:
            try:
                deadline = timezone.datetime.strptime(deadline_str, '%Y-%m-%d').date()
            except ValueError:
                deadline = None

        job = Job.objects.create(
            company=profile.company,
            recruiter=profile,
            title=title,
            job_type=job_type,
            workplace_type=workplace_type,
            location=location,
            salary_range=salary_range,
            eligible_branches=eligible_branches,
            min_cgpa=min_cgpa_dec,
            description=description,
            responsibilities=responsibilities,
            requirements=requirements,
            deadline=deadline,
            is_active=True
        )

        if skill_ids:
            job.required_skills.set(skill_ids)

        messages.success(request, f"Engineering job vacancy '{job.title}' has been successfully published!")
        return redirect('recruiters:dashboard')

    from jobs.models import Skill
    skills = Skill.objects.all()
    return render(request, 'recruiters/post_job.html', {
        'profile': profile,
        'company': profile.company,
        'skills': skills,
    })
