from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    # Main VEX AI Workspace
    path('', views.workspace_view, name='workspace'),

    # Conversation Management API
    path('api/conversations/', views.api_conversations_list, name='api_conversations_list'),
    path('api/conversations/<int:conversation_id>/', views.api_conversation_detail, name='api_conversation_detail'),
    path('api/conversations/<int:conversation_id>/delete/', views.api_conversation_delete, name='api_conversation_delete'),

    # Chat & Action Execution API
    path('api/send/', views.api_send_message, name='api_send_message'),
    path('api/quick-action/', views.api_quick_action, name='api_quick_action'),

    # Student Memory Management API
    path('api/memories/', views.api_memories_list, name='api_memories_list'),
    path('api/memories/<int:memory_id>/toggle/', views.api_memory_toggle, name='api_memory_toggle'),
    path('api/memories/<int:memory_id>/delete/', views.api_memory_delete, name='api_memory_delete'),

    # Message Feedback
    path('api/messages/<int:message_id>/feedback/', views.api_message_feedback, name='api_message_feedback'),
]

