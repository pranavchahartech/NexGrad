from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.utils import timezone
from .models import (
    Challenge, ChallengeAssignment, ChallengeSubmission,
    ChallengeEvaluation, ChallengeEvent
)
from .forms import ChallengeSubmissionForm
from students.models import StudentProfile
from applications.models import Application
from notifications.models import Notification

def get_student_profile_or_deny(user):
    """Enforces that the authenticated user is a registered engineering student."""
    if not user.is_authenticated or not hasattr(user, 'is_student') or not user.is_student:
        raise PermissionDenied("Access restricted to registered engineering students.")
    profile = getattr(user, 'student_profile', None)
    if not profile:
        raise PermissionDenied("Student profile not found for this account.")
    return profile


@login_required
def student_my_challenges(request):
    """
    Student Dashboard Section: 'MY SELECTED CHALLENGES'
    STRICT PRIVACY: Displays exclusively challenges assigned directly to the authenticated student.
    """
    profile = get_student_profile_or_deny(request.user)
    status_filter = request.GET.get('status', 'ALL').upper()

    assignments_qs = ChallengeAssignment.objects.filter(
        student=profile
    ).select_related(
        'challenge', 'challenge__recruiter__company', 'challenge__job'
    ).prefetch_related('submissions', 'submissions__evaluation')

    # Apply tab filter
    if status_filter == 'NEW':
        assignments_qs = assignments_qs.filter(status=ChallengeAssignment.Status.ASSIGNED)
    elif status_filter == 'IN_PROGRESS':
        assignments_qs = assignments_qs.filter(status=ChallengeAssignment.Status.IN_PROGRESS)
    elif status_filter == 'SUBMITTED':
        assignments_qs = assignments_qs.filter(status=ChallengeAssignment.Status.SUBMITTED)
    elif status_filter == 'UNDER_REVIEW':
        assignments_qs = assignments_qs.filter(status=ChallengeAssignment.Status.UNDER_REVIEW)
    elif status_filter == 'EVALUATED':
        assignments_qs = assignments_qs.filter(status=ChallengeAssignment.Status.EVALUATED)
    elif status_filter == 'REVOKED':
        assignments_qs = assignments_qs.filter(status=ChallengeAssignment.Status.REVOKED)

    # Counts for tab badges
    base_qs = ChallengeAssignment.objects.filter(student=profile)
    counts = {
        'ALL': base_qs.count(),
        'NEW': base_qs.filter(status=ChallengeAssignment.Status.ASSIGNED).count(),
        'IN_PROGRESS': base_qs.filter(status=ChallengeAssignment.Status.IN_PROGRESS).count(),
        'SUBMITTED': base_qs.filter(status=ChallengeAssignment.Status.SUBMITTED).count(),
        'UNDER_REVIEW': base_qs.filter(status=ChallengeAssignment.Status.UNDER_REVIEW).count(),
        'EVALUATED': base_qs.filter(status=ChallengeAssignment.Status.EVALUATED).count(),
    }

    return render(request, 'challenges/student/my_challenges.html', {
        'assignments': assignments_qs,
        'status_filter': status_filter,
        'counts': counts,
        'title': 'My Selected Challenges'
    })


@login_required
def student_challenge_detail(request, assignment_id):
    """
    Detailed challenge briefing page for the assigned student.
    Enforces that only the student explicitly assigned to this challenge can view it.
    """
    profile = get_student_profile_or_deny(request.user)
    assignment = get_object_or_404(
        ChallengeAssignment.objects.select_related(
            'challenge', 'challenge__recruiter__company', 'challenge__job'
        ).prefetch_related('challenge__attachments', 'submissions'),
        id=assignment_id
    )

    # Server-side authorization check (Rule 3 & Rule 5)
    if assignment.student != profile:
        raise PermissionDenied("You do not have access to this private assessment.")

    latest_submission = assignment.latest_submission
    evaluation = getattr(latest_submission, 'evaluation', None) if latest_submission else None

    return render(request, 'challenges/student/challenge_detail.html', {
        'assignment': assignment,
        'challenge': assignment.challenge,
        'latest_submission': latest_submission,
        'evaluation': evaluation,
        'title': f"Challenge: {assignment.challenge.title}"
    })


@login_required
def student_challenge_start(request, assignment_id):
    """
    Candidate starts the challenge. Transitions assignment status to IN_PROGRESS.
    """
    profile = get_student_profile_or_deny(request.user)
    assignment = get_object_or_404(ChallengeAssignment, id=assignment_id)

    if assignment.student != profile:
        raise PermissionDenied("You do not have access to this private assessment.")

    if assignment.status == ChallengeAssignment.Status.REVOKED:
        messages.error(request, "This assignment has been revoked by the recruiter.")
        return redirect('challenges:student_my_challenges')

    if assignment.status == ChallengeAssignment.Status.ASSIGNED:
        assignment.status = ChallengeAssignment.Status.IN_PROGRESS
        assignment.started_at = timezone.now()
        assignment.save()

        ChallengeEvent.objects.create(
            assignment=assignment,
            actor=request.user,
            event_type=ChallengeEvent.EventType.CHALLENGE_STARTED,
            description=f"Candidate {request.user.get_full_name() or request.user.username} officially started the challenge."
        )
        messages.info(request, "Challenge active! Review instructions carefully and submit your solution before the deadline.")

    return redirect('challenges:student_challenge_submit', assignment_id=assignment.id)


@login_required
def student_challenge_submit(request, assignment_id):
    """
    Solution Submission Interface:
    Accepts code files, repositories, demo links, architecture descriptions, and documentation.
    Enforces server-side deadline cutoff and resubmission permissions.
    """
    profile = get_student_profile_or_deny(request.user)
    assignment = get_object_or_404(
        ChallengeAssignment.objects.select_related('challenge', 'challenge__recruiter__company'),
        id=assignment_id
    )

    # Server-side authorization check
    if assignment.student != profile:
        raise PermissionDenied("You do not have access to this private assessment.")

    # Rule 6: Check revocation
    if assignment.status == ChallengeAssignment.Status.REVOKED:
        messages.error(request, "This assignment was revoked by the recruiter. Submissions are no longer permitted.")
        return redirect('challenges:student_my_challenges')

    # Rule 7: Server-side deadline enforcement
    if assignment.is_deadline_passed:
        messages.error(request, "The submission deadline for this challenge has expired. Submissions are closed.")
        return redirect('challenges:student_challenge_detail', assignment_id=assignment.id)

    # Resubmission permission check
    existing_submissions = assignment.submissions.all()
    if existing_submissions.exists() and not assignment.challenge.allow_resubmission:
        messages.warning(request, "You have already submitted a solution for this challenge. Re-submissions are not permitted.")
        return redirect('challenges:student_challenge_detail', assignment_id=assignment.id)

    if request.method == 'POST':
        form = ChallengeSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            sub_count = existing_submissions.count() + 1
            submission = form.save(commit=False)
            submission.assignment = assignment
            submission.submission_number = sub_count
            submission.status = ChallengeSubmission.Status.SUBMITTED
            submission.save()

            # Update assignment status
            assignment.status = ChallengeAssignment.Status.SUBMITTED
            assignment.save()

            # Update application status to UNDER_REVIEW
            if assignment.application:
                assignment.application.status = Application.Status.UNDER_REVIEW
                assignment.application.save()

            # Audit event
            event_type = ChallengeEvent.EventType.SUBMISSION_UPDATED if sub_count > 1 else ChallengeEvent.EventType.SUBMISSION_UPLOADED
            ChallengeEvent.objects.create(
                assignment=assignment,
                actor=request.user,
                event_type=event_type,
                description=f"Candidate submitted solution #{sub_count}."
            )

            # In-Platform Notification to Recruiter
            recruiter_user = assignment.challenge.recruiter.user
            Notification.objects.create(
                recipient=recruiter_user,
                title=f"New Challenge Submission: {assignment.challenge.title}",
                message=(
                    f"Candidate {request.user.get_full_name() or request.user.username} has submitted their solution "
                    f"(Submission #{sub_count}) for '{assignment.challenge.title}'."
                ),
                notification_type='APPLICATION'
            )

            messages.success(request, f"Solution #{sub_count} submitted successfully! Your recruiter has been notified.")
            return redirect('challenges:student_submission_detail', submission_id=submission.id)
    else:
        form = ChallengeSubmissionForm()

    return render(request, 'challenges/student/challenge_submit.html', {
        'form': form,
        'assignment': assignment,
        'challenge': assignment.challenge,
        'submission_number': existing_submissions.count() + 1,
        'title': f"Submit Solution: {assignment.challenge.title}"
    })


@login_required
def student_submission_detail(request, submission_id):
    """
    Candidate inspects their submitted solution and evaluation (if released).
    """
    profile = get_student_profile_or_deny(request.user)
    submission = get_object_or_404(
        ChallengeSubmission.objects.select_related(
            'assignment', 'assignment__challenge', 'assignment__student',
            'assignment__challenge__recruiter__company'
        ),
        id=submission_id
    )

    # Server-side authorization check (Rule 5)
    if submission.assignment.student != profile:
        raise PermissionDenied("You do not have permission to view submissions belonging to other candidates.")

    evaluation = getattr(submission, 'evaluation', None)
    # Only show evaluation if it has been published
    if evaluation and evaluation.evaluation_status != ChallengeEvaluation.EvaluationStatus.PUBLISHED:
        evaluation = None

    return render(request, 'challenges/student/submission_detail.html', {
        'submission': submission,
        'assignment': submission.assignment,
        'challenge': submission.assignment.challenge,
        'evaluation': evaluation,
        'title': f"Submission #{submission.submission_number} - {submission.assignment.challenge.title}"
    })


@login_required
def student_challenge_feedback(request, assignment_id):
    """
    Candidate views detailed recruiter marks, criteria scores, strengths, and feedback.
    """
    profile = get_student_profile_or_deny(request.user)
    assignment = get_object_or_404(ChallengeAssignment, id=assignment_id)

    if assignment.student != profile:
        raise PermissionDenied("You do not have access to this assessment.")

    latest_submission = assignment.latest_submission
    evaluation = getattr(latest_submission, 'evaluation', None) if latest_submission else None

    if not evaluation or evaluation.evaluation_status != ChallengeEvaluation.EvaluationStatus.PUBLISHED:
        messages.info(request, "Evaluation results have not been released by the recruiter yet.")
        return redirect('challenges:student_challenge_detail', assignment_id=assignment.id)

    return render(request, 'challenges/student/submission_feedback.html', {
        'assignment': assignment,
        'challenge': assignment.challenge,
        'submission': latest_submission,
        'evaluation': evaluation,
        'title': f"Evaluation Feedback: {assignment.challenge.title}"
    })

