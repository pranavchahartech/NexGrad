import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from students.models import StudentProfile
from .models import (
    AIConversation,
    AIMessage,
    StudentAIMemory,
    AIMessageFeedback
)
from .services import (
    gemini_client,
    VEXContextService,
    VEXMemoryService,
    VEXConversationService
)


def _get_student_profile(user):
    """Safely retrieves or creates StudentProfile for the logged-in user."""
    profile, _ = StudentProfile.objects.get_or_create(user=user)
    return profile


@login_required
def workspace_view(request):
    """
    Renders the dedicated VEX AI Assistant Workspace.
    """
    student = _get_student_profile(request.user)
    conversations = AIConversation.objects.filter(
        student=student,
        is_archived=False
    ).order_by('-updated_at')

    # Support opening a specific ongoing conversation from the popup widget
    conv_param = request.GET.get('conv')
    active_conversation = None
    if conv_param:
        try:
            active_conversation = conversations.filter(id=int(conv_param)).first()
        except (ValueError, TypeError):
            pass

    if not active_conversation:
        active_conversation = conversations.first()

    if not active_conversation:
        active_conversation = AIConversation.objects.create(
            student=student,
            title='Career & Learning Consultation'
        )
        conversations = [active_conversation]

    memories = VEXMemoryService.get_student_memories(student, include_inactive=True)
    summary = VEXContextService.get_student_summary(student)

    return render(request, 'ai_assistant/workspace.html', {
        'student': student,
        'summary': summary,
        'active_conversation': active_conversation,
        'conversations': conversations,
        'memories': memories,
        'gemini_configured': gemini_client.is_configured,
        'gemini_model': gemini_client.model_name,
        'title': 'Novus — AI Career Companion | NexGrad',
    })


def api_conversations_list(request):
    """
    Returns JSON list of conversations for the authenticated student.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'conversations': [], 'auth_required': True}, status=401)

    student = _get_student_profile(request.user)
    conversations = AIConversation.objects.filter(
        student=student,
        is_archived=False
    ).values('id', 'title', 'updated_at', 'is_pinned')
    return JsonResponse({'conversations': list(conversations)})


def api_conversation_detail(request, conversation_id):
    """
    Returns messages for a specific conversation. Strictly student-isolated.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.', 'auth_required': True}, status=401)

    student = _get_student_profile(request.user)
    conversation = get_object_or_404(AIConversation, id=conversation_id, student=student)
    messages = conversation.messages.all().order_by('created_at')

    msg_list = []
    for m in messages:
        msg_list.append({
            'id': m.id,
            'role': m.role,
            'content': m.content,
            'structured_data': m.structured_data,
            'tokens_used': m.tokens_used,
            'created_at': m.created_at.strftime('%H:%M'),
        })

    return JsonResponse({
        'conversation_id': conversation.id,
        'title': conversation.title,
        'messages': msg_list
    })


@require_POST
def api_conversation_delete(request, conversation_id):
    """
    Soft-archives or deletes a student conversation. Strictly student-isolated.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required.'}, status=401)

    student = _get_student_profile(request.user)
    conversation = get_object_or_404(AIConversation, id=conversation_id, student=student)
    conversation.is_archived = True
    conversation.save(update_fields=['is_archived'])
    return JsonResponse({'status': 'success', 'message': 'Conversation deleted.'})


@require_POST
def api_send_message(request):
    """
    Primary chat endpoint. Ingests user message, invokes VEXConversationService,
    and returns assistant reply with structured UI components.
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'error': 'Please sign in to chat with Novus and get personalized career guidance.',
            'auth_required': True
        }, status=401)

    student = _get_student_profile(request.user)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        body = request.POST

    message_text = body.get('message', '').strip()
    conversation_id = body.get('conversation_id')
    context_action = body.get('action')
    action_params = body.get('params', {})

    if not message_text and not context_action:
        return JsonResponse({'error': 'Message content cannot be empty.'}, status=400)

    try:
        response_data = VEXConversationService.process_message(
            student=student,
            message_text=message_text,
            conversation_id=conversation_id,
            context_action=context_action,
            action_params=action_params
        )
        return JsonResponse({'status': 'success', **response_data})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e)}, status=500)


@require_POST
def api_quick_action(request):
    """
    Executes quick one-click actions (e.g. Find Jobs, Skill Gap, Create Roadmap).
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'error': 'Please sign in to execute career actions with Novus.',
            'auth_required': True
        }, status=401)

    student = _get_student_profile(request.user)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        body = request.POST

    action = body.get('action')
    params = body.get('params', {})
    conversation_id = body.get('conversation_id')

    action_prompts = {
        'find_jobs': "Find matching jobs for my profile and explain my eligibility.",
        'find_internships': "Find high-affinity internships suited for my current semester.",
        'skill_gap': f"Perform a technical skill gap analysis for {params.get('target_role', 'Backend Engineer')}.",
        'create_roadmap': f"Generate a structured learning roadmap to prepare for {params.get('target_role', 'Full Stack Developer')}.",
        'mock_interview': f"Start a technical mock interview for {params.get('target_role', 'Software Engineer')}.",
        'analyse_resume': "Audit my resume and portfolio against current industry criteria.",
        'my_applications': "Review my active job application statuses and next steps.",
    }

    message_text = action_prompts.get(action, "What should I focus on next in my engineering career?")

    response_data = VEXConversationService.process_message(
        student=student,
        message_text=message_text,
        conversation_id=conversation_id,
        context_action=action,
        action_params=params
    )
    return JsonResponse({'status': 'success', **response_data})


@login_required
def api_memories_list(request):
    """
    Returns student-inspectable long-term memories.
    """
    student = _get_student_profile(request.user)
    memories = VEXMemoryService.get_student_memories(student, include_inactive=True)

    data = [
        {
            'id': m.id,
            'category': m.get_category_display(),
            'key': m.key,
            'value': m.value,
            'is_active': m.is_active,
            'updated_at': m.updated_at.strftime('%b %d, %Y'),
        }
        for m in memories
    ]
    return JsonResponse({'memories': data})


@login_required
@require_POST
def api_memory_toggle(request, memory_id):
    """
    Toggles an active/inactive memory key. Strictly student-isolated.
    """
    student = _get_student_profile(request.user)
    mem = VEXMemoryService.toggle_memory(student, memory_id)
    if not mem:
        return JsonResponse({'error': 'Memory item not found or unauthorized.'}, status=404)

    return JsonResponse({
        'status': 'success',
        'id': mem.id,
        'is_active': mem.is_active,
        'message': f"Memory '{mem.key}' is now {'active' if mem.is_active else 'paused'}."
    })


@login_required
@require_POST
def api_memory_delete(request, memory_id):
    """
    Deletes a memory item. Strictly student-isolated.
    """
    student = _get_student_profile(request.user)
    success = VEXMemoryService.delete_memory(student, memory_id)
    if not success:
        return JsonResponse({'error': 'Memory item not found or unauthorized.'}, status=404)

    return JsonResponse({'status': 'success', 'message': 'Memory deleted permanently.'})


@login_required
@require_POST
def api_message_feedback(request, message_id):
    """
    Saves student thumbs up/down rating for a VEX response.
    """
    student = _get_student_profile(request.user)
    message = get_object_or_404(AIMessage, id=message_id, conversation__student=student)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except Exception:
        body = request.POST

    is_helpful = bool(body.get('is_helpful', True))
    feedback_text = body.get('feedback_text', '').strip()

    AIMMessageFeedback.objects.update_or_create(
        message=message,
        defaults={
            'is_helpful': is_helpful,
            'feedback_text': feedback_text
        }
    )

    return JsonResponse({'status': 'success', 'message': 'Thank you for your feedback!'})
