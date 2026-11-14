from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import (
    Challenge, ChallengeAttachment, ChallengeAssignment,
    ChallengeSubmission, ChallengeEvaluation, ChallengeEvent
)
from .forms import ChallengeForm, ChallengeAttachmentForm, ChallengeEvaluationForm
from recruiters.models import RecruiterProfile
from applications.models import Application, ApplicationStatusHistory
from notifications.models import Notification

def get_recruiter_profile_or_deny(user):
    """Enforces that the authenticated user is a verified recruiter with a profile."""
    if not user.is_authenticated or not hasattr(user, 'is_recruiter') or not user.is_recruiter:
        raise PermissionDenied("Access restricted to registered company recruiters.")
    profile = getattr(user, 'recruiter_profile', None)
    if not profile:
        raise PermissionDenied("Recruiter profile not found for this account.")
    return profile


@login_required
def recruiter_challenge_list(request):
    """
    Recruiter Dashboard: 'CHALLENGE MANAGEMENT'
    Displays all challenges authored by the authenticated recruiter.
    """
    profile = get_recruiter_profile_or_deny(request.user)
    status_filter = request.GET.get('status', 'ALL')

    challenges_qs = Challenge.objects.filter(recruiter=profile).select_related('job', 'recruiter__company')
    if status_filter != 'ALL':
        challenges_qs = challenges_qs.filter(status=status_filter)

    # Aggregate counts
    all_challenges = Challenge.objects.filter(recruiter=profile)
    total_challenges = all_challenges.count()
    active_published = all_challenges.filter(status=Challenge.Status.PUBLISHED).count()
    total_assignments = ChallengeAssignment.objects.filter(challenge__recruiter=profile).exclude(status=ChallengeAssignment.Status.REVOKED).count()
    total_submissions = ChallengeSubmission.objects.filter(assignment__challenge__recruiter=profile).count()
    pending_evaluations = ChallengeAssignment.objects.filter(
        challenge__recruiter=profile,
        status__in=[ChallengeAssignment.Status.SUBMITTED, ChallengeAssignment.Status.UNDER_REVIEW]
    ).count()

    return render(request, 'challenges/recruiter/challenge_list.html', {
        'challenges': challenges_qs,
        'status_filter': status_filter,
        'total_challenges': total_challenges,
        'active_published': active_published,
        'total_assignments': total_assignments,
        'total_submissions': total_submissions,
        'pending_evaluations': pending_evaluations,
        'title': 'Challenge Management Dashboard'
    })


@login_required
def recruiter_challenge_create(request):
    """
    Recruiter creates a new private technical challenge.
    """
    profile = get_recruiter_profile_or_deny(request.user)

    if request.method == 'POST':
        form = ChallengeForm(request.POST, recruiter_profile=profile)
        attachment_form = ChallengeAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.recruiter = profile
            challenge.save()

            # Handle optional supporting attachment
            if attachment_form.is_valid() and request.FILES.get('file'):
                attachment = attachment_form.save(commit=False)
                attachment.challenge = challenge
                attachment.save()

            messages.success(request, f"Challenge '{challenge.title}' created successfully as {challenge.get_status_display()}!")
            return redirect('challenges:recruiter_challenge_detail', challenge_id=challenge.id)
    else:
        form = ChallengeForm(recruiter_profile=profile)
        attachment_form = ChallengeAttachmentForm()

    return render(request, 'challenges/recruiter/challenge_create.html', {
        'form': form,
        'attachment_form': attachment_form,
        'title': 'Create Private Technical Challenge'
    })


@login_required
def recruiter_challenge_edit(request, challenge_id):
    """
    Recruiter edits an existing challenge they authored.
    """
    profile = get_recruiter_profile_or_deny(request.user)
    challenge = get_object_or_404(Challenge, id=challenge_id)

    # Server-side ownership verification
    if challenge.recruiter != profile:
        raise PermissionDenied("You do not have permission to modify challenges created by another recruiter.")

    if request.method == 'POST':
        form = ChallengeForm(request.POST, instance=challenge, recruiter_profile=profile)
        if form.is_valid():
            form.save()
            messages.success(request, f"Challenge '{challenge.title}' updated successfully.")
            return redirect('challenges:recruiter_challenge_detail', challenge_id=challenge.id)
    else:
        form = ChallengeForm(instance=challenge, recruiter_profile=profile)

    return render(request, 'challenges/recruiter/challenge_edit.html', {
        'form': form,
        'challenge': challenge,
        'title': f"Edit: {challenge.title}"
    })


@login_required
def recruiter_challenge_detail(request, challenge_id):
    """
    Challenge overview, candidate assignments table, and status tracking.
    """
    profile = get_recruiter_profile_or_deny(request.user)
    challenge = get_object_or_404(Challenge, id=challenge_id)

    if challenge.recruiter != profile:
        raise PermissionDenied("You do not have permission to access this challenge.")

    assignments = challenge.assignments.select_related('student', 'student__user', 'student__institution', 'application').prefetch_related('submissions')
    attachments = challenge.attachments.all()

    return render(request, 'challenges/recruiter/challenge_detail.html', {
        'challenge': challenge,
        'assignments': assignments,
        'attachments': attachments,
        'title': f"Challenge Overview: {challenge.title}"
    })


@login_required
def recruiter_challenge_assign(request, challenge_id):
    """
    Candidate Assignment Interface:
    Allows recruiter to select specific shortlisted candidates and create ChallengeAssignment records.
    """
    profile = get_recruiter_profile_or_deny(request.user)
    challenge = get_object_or_404(Challenge, id=challenge_id)

    if challenge.recruiter != profile:
        raise PermissionDenied("You do not have permission to assign candidates to this challenge.")

    # Find candidates eligible for assignment:
    # Applications for the associated job (or recruiter's jobs)
    if challenge.job:
        candidate_apps = Application.objects.filter(job=challenge.job).select_related(
            'student', 'student__user', 'student__institution', 'job'
        )
    else:
        candidate_apps = Application.objects.filter(
            job__recruiter=profile
        ).select_related('student', 'student__user', 'student__institution', 'job')

    # Get already assigned student IDs to indicate in UI
    assigned_student_ids = set(
        challenge.assignments.exclude(status=ChallengeAssignment.Status.REVOKED).values_list('student_id', flat=True)
    )

    if request.method == 'POST':
        selected_app_ids = request.POST.getlist('selected_applications')
        custom_deadline_str = request.POST.get('custom_deadline')
        
        # Determine deadline: custom or challenge's default
        if custom_deadline_str:
            try:
                deadline = timezone.datetime.fromisoformat(custom_deadline_str)
                if timezone.is_naive(deadline):
                    deadline = timezone.make_aware(deadline)
            except Exception:
                deadline = challenge.deadline
        else:
            deadline = challenge.deadline

        assigned_count = 0
        with transaction.atomic():
            for app_id in selected_app_ids:
                app = candidate_apps.filter(id=app_id).first()
                if not app:
                    continue

                student = app.student
                # Prevent duplicate active assignments
                existing = ChallengeAssignment.objects.filter(
                    challenge=challenge,
                    student=student,
                    status__in=[
                        ChallengeAssignment.Status.ASSIGNED,
                        ChallengeAssignment.Status.IN_PROGRESS,
                        ChallengeAssignment.Status.SUBMITTED,
                        ChallengeAssignment.Status.UNDER_REVIEW,
                        ChallengeAssignment.Status.EVALUATED
                    ]
                ).first()

                if existing:
                    continue

                assignment = ChallengeAssignment.objects.create(
                    challenge=challenge,
                    student=student,
                    application=app,
                    assigned_by=request.user,
                    deadline=deadline,
                    status=ChallengeAssignment.Status.ASSIGNED
                )

                # Update recruitment status to SHORTLISTED / ASSESSMENT
                app.status = Application.Status.ASSESSMENT
                app.save()

                ApplicationStatusHistory.objects.create(
                    application=app,
                    from_status=app.status,
                    to_status=Application.Status.ASSESSMENT,
                    updated_by=request.user,
                    notes=f"Private technical challenge assigned: '{challenge.title}'."
                )

                # Create Audit Event
                ChallengeEvent.objects.create(
                    assignment=assignment,
                    actor=request.user,
                    event_type=ChallengeEvent.EventType.CHALLENGE_ASSIGNED,
                    description=f"Recruiter assigned challenge '{challenge.title}' to candidate {student.user.get_full_name() or student.user.username}."
                )

                # Generate In-Platform Notification for Student
                company_name = challenge.recruiter.company.name if challenge.recruiter.company else "the recruiter"
                job_title = challenge.job.title if challenge.job else "the position"
                formatted_deadline = deadline.strftime("%b %d, %Y at %I:%M %p")

                Notification.objects.create(
                    recipient=student.user,
                    title=f"Technical Challenge Assigned: {challenge.title}",
                    message=(
                        f"Congratulations! You have been shortlisted for the {job_title} position at {company_name}. "
                        f"The recruiter has assigned you a private technical challenge as the next stage of the recruitment process. "
                        f"Please review the instructions and submit your solution before {formatted_deadline}."
                    ),
                    notification_type='ASSESSMENT'
                )

                assigned_count += 1

        if assigned_count > 0:
            messages.success(request, f"Successfully assigned challenge to {assigned_count} candidate(s). In-platform notifications dispatched.")
        else:
            messages.info(request, "No new candidates were assigned (already assigned or none selected).")

        return redirect('challenges:recruiter_challenge_detail', challenge_id=challenge.id)

    return render(request, 'challenges/recruiter/challenge_assign.html', {
        'challenge': challenge,
        'candidate_apps': candidate_apps,
        'assigned_student_ids': assigned_student_ids,
        'title': f"Assign Candidates: {challenge.title}"
    })


@login_required
def recruiter_challenge_submissions(request, challenge_id):
    """
    Submission Management: Lists all submissions received for a specific challenge.
    """
    profile = get_recruiter_profile_or_deny(request.user)
    challenge = get_object_or_404(Challenge, id=challenge_id)

    if challenge.recruiter != profile:
        raise PermissionDenied("You do not have permission to view submissions for this challenge.")

    submissions = ChallengeSubmission.objects.filter(
        assignment__challenge=challenge
    ).select_related(
        'assignment', 'assignment__student', 'assignment__student__user',
        'assignment__student__institution', 'evaluation'
    )

    return render(request, 'challenges/recruiter/submission_list.html', {
        'challenge': challenge,
        'submissions': submissions,
        'title': f"Submissions for {challenge.title}"
    })


@login_required
def recruiter_submission_evaluate(request, submission_id):
    """
    Evaluation Centre: Evaluates a candidate's solution with marks rubric, feedback, and stage advancement.
    """
    profile = get_recruiter_profile_or_deny(request.user)
    submission = get_object_or_404(
        ChallengeSubmission.objects.select_related(
            'assignment', 'assignment__challenge', 'assignment__student',
            'assignment__student__user', 'assignment__application'
        ),
        id=submission_id
    )

    # Server-side verification: recruiter must own this challenge
    if submission.assignment.challenge.recruiter != profile:
        raise PermissionDenied("You cannot evaluate submissions for challenges belonging to another recruiter.")

    evaluation, created = ChallengeEvaluation.objects.get_or_create(
        submission=submission,
        defaults={'evaluator': request.user}
    )

    if request.method == 'POST':
        form = ChallengeEvaluationForm(request.POST, instance=evaluation)
        if form.is_valid():
            eval_obj = form.save(commit=False)
            eval_obj.evaluator = request.user
            eval_obj.save()

            assignment = submission.assignment
            challenge = assignment.challenge

            if eval_obj.evaluation_status == ChallengeEvaluation.EvaluationStatus.PUBLISHED:
                assignment.status = ChallengeAssignment.Status.EVALUATED
                assignment.save()

                submission.status = ChallengeSubmission.Status.EVALUATED
                submission.save()

                # Optional recruitment stage transition based on recommendation
                app = assignment.application
                if app:
                    if eval_obj.recommended_stage == ChallengeEvaluation.RecommendedStage.SCHEDULE_INTERVIEW:
                        app.status = Application.Status.INTERVIEW
                        app.save()
                        ApplicationStatusHistory.objects.create(
                            application=app,
                            from_status=Application.Status.ASSESSMENT,
                            to_status=Application.Status.INTERVIEW,
                            updated_by=request.user,
                            notes=f"Candidate cleared technical challenge '{challenge.title}' with score {eval_obj.total_marks}/{challenge.maximum_marks}."
                        )
                    elif eval_obj.recommended_stage == ChallengeEvaluation.RecommendedStage.OFFER_POSITION:
                        app.status = Application.Status.SELECTED
                        app.save()
                    elif eval_obj.recommended_stage == ChallengeEvaluation.RecommendedStage.NOT_RECOMMENDED:
                        app.status = Application.Status.REJECTED
                        app.save()

                # Audit Event
                ChallengeEvent.objects.create(
                    assignment=assignment,
                    actor=request.user,
                    event_type=ChallengeEvent.EventType.EVALUATION_PUBLISHED,
                    description=f"Recruiter published evaluation: {eval_obj.total_marks}/{challenge.maximum_marks}. Recommendation: {eval_obj.get_recommended_stage_display()}."
                )

                # Send Notification to Candidate
                Notification.objects.create(
                    recipient=assignment.student.user,
                    title=f"Challenge Evaluated: {challenge.title}",
                    message=(
                        f"Your submission for '{challenge.title}' at {challenge.recruiter.company.name if challenge.recruiter.company else 'the company'} "
                        f"has been evaluated! Score: {eval_obj.total_marks}/{challenge.maximum_marks}. "
                        f"View detailed feedback and next steps in your dashboard."
                    ),
                    notification_type='ASSESSMENT'
                )

                messages.success(request, f"Evaluation published to candidate! Score: {eval_obj.total_marks}/{challenge.maximum_marks}.")
            else:
                ChallengeEvent.objects.create(
                    assignment=assignment,
                    actor=request.user,
                    event_type=ChallengeEvent.EventType.EVALUATION_SAVED,
                    description=f"Recruiter saved draft evaluation ({eval_obj.total_marks} marks)."
                )
                messages.info(request, "Evaluation draft saved. It remains private to your hiring team.")

            return redirect('challenges:recruiter_challenge_detail', challenge_id=challenge.id)
    else:
        form = ChallengeEvaluationForm(instance=evaluation)

    return render(request, 'challenges/recruiter/submission_evaluate.html', {
        'submission': submission,
        'evaluation': evaluation,
        'form': form,
        'challenge': submission.assignment.challenge,
        'title': f"Evaluate: {submission.assignment.student.user.get_full_name() or submission.assignment.student.user.username}"
    })


@login_required
def recruiter_assignment_revoke(request, assignment_id):
    """
    Revokes an assignment, revoking the student's access to submit solutions.
    """
    profile = get_recruiter_profile_or_deny(request.user)
    assignment = get_object_or_404(ChallengeAssignment, id=assignment_id)

    if assignment.challenge.recruiter != profile:
        raise PermissionDenied("You do not have permission to revoke assignments for this challenge.")

    if request.method == 'POST':
        reason = request.POST.get('revocation_reason', 'Assignment revoked by hiring team.')
        assignment.status = ChallengeAssignment.Status.REVOKED
        assignment.revoked_at = timezone.now()
        assignment.revoked_by = request.user
        assignment.revocation_reason = reason
        assignment.save()

        ChallengeEvent.objects.create(
            assignment=assignment,
            actor=request.user,
            event_type=ChallengeEvent.EventType.ASSIGNMENT_REVOKED,
            description=f"Assignment revoked by recruiter. Reason: {reason}"
        )

        messages.warning(request, f"Assignment for {assignment.student.user.get_full_name() or assignment.student.user.username} has been revoked.")

    return redirect('challenges:recruiter_challenge_detail', challenge_id=assignment.challenge.id)

