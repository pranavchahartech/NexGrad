from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Assessment, AssessmentAttempt, DeviceTelemetry
from students.models import StudentProfile

def assessment_list(request):
    assessments = Assessment.objects.filter(is_active=True)
    return render(request, 'assessments/list.html', {
        'assessments': assessments,
        'active_page': 'assessments',
    })

def assessment_detail(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)
    return render(request, 'assessments/detail.html', {
        'assessment': assessment,
    })

@login_required
def take_assessment(request, assessment_id):
    """
    Device-Neutral Assessment Runtime Execution (Part 9 Research Module).
    Collects client execution telemetry for measurement equivalence research.
    """
    assessment = get_object_or_404(Assessment, id=assessment_id)
    student_profile = get_object_or_404(StudentProfile, user=request.user)

    if request.method == 'POST':
        code_solution = request.POST.get('code_solution', '').strip()
        viewport_w = int(request.POST.get('viewport_w', 1920) or 1920)
        viewport_h = int(request.POST.get('viewport_h', 1080) or 1080)
        input_modality = request.POST.get('input_modality', 'Keyboard + Mouse')
        latency_ms = int(request.POST.get('latency_ms', 35) or 35)
        interaction_count = int(request.POST.get('interaction_count', 12) or 12)

        # Basic algorithmic evaluation heuristic
        score = 85 if len(code_solution) > 30 else 50
        is_passed = score >= assessment.passing_marks

        attempt = AssessmentAttempt.objects.create(
            assessment=assessment,
            student=student_profile,
            score=score,
            is_passed=is_passed,
            completed_at=timezone.now()
        )

        DeviceTelemetry.objects.create(
            attempt=attempt,
            viewport_width=viewport_w,
            viewport_height=viewport_h,
            input_modality=input_modality,
            interaction_count=interaction_count,
            round_trip_latency_ms=latency_ms
        )

        messages.success(request, f"Assessment completed! Your score: {score}% ({'PASSED' if is_passed else 'NEEDS RETAKE'})")
        return redirect('assessments:result', attempt_id=attempt.id)

    return render(request, 'assessments/take.html', {
        'assessment': assessment,
        'profile': student_profile,
    })

@login_required
def assessment_result(request, attempt_id):
    attempt = get_object_or_404(AssessmentAttempt.objects.select_related('assessment', 'telemetry', 'student'), id=attempt_id)
    return render(request, 'assessments/result.html', {
        'attempt': attempt,
    })
