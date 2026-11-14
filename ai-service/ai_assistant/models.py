from django.db import models
from django.conf import settings
from django.utils import timezone


class AIConversation(models.Model):
    """
    Persistent conversational session for a student with VEX.
    """
    student = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='ai_conversations'
    )
    title = models.CharField(max_length=255, default='Career & Learning Consultation')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.student.user.username} - {self.title} ({self.created_at.strftime('%b %d')})"

    @property
    def current_state(self):
        state, _ = ConversationState.objects.get_or_create(conversation=self)
        return state


class ConversationState(models.Model):
    """
    Maintains persistent, structured conversation context, active intents,
    tasks, entity references, and tool results across turns.
    """
    conversation = models.OneToOneField(
        AIConversation,
        on_delete=models.CASCADE,
        related_name='state'
    )
    active_intent = models.CharField(max_length=100, blank=True, default='')
    active_task = models.CharField(max_length=100, blank=True, default='')
    active_entity_type = models.CharField(max_length=50, blank=True, default='')
    active_entity_ids = models.JSONField(default=list, blank=True)
    last_tool_called = models.CharField(max_length=100, blank=True, default='')
    last_tool_payload = models.JSONField(default=dict, blank=True)
    context_summary = models.TextField(blank=True, default='')
    conversation_status = models.CharField(max_length=50, default='active')
    metadata = models.JSONField(default=dict, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"State for Conv {self.conversation.id}: {self.active_intent} ({self.active_task})"

    def to_dict(self):
        return {
            'conversation_id': self.conversation.id,
            'student_id': self.conversation.student.id,
            'active_intent': self.active_intent,
            'active_task': self.active_task,
            'active_entity_type': self.active_entity_type,
            'active_entity_ids': self.active_entity_ids,
            'last_tool_called': self.last_tool_called,
            'context_summary': self.context_summary,
            'conversation_status': self.conversation_status,
            'metadata': self.metadata,
        }


class AIMessage(models.Model):
    """
    Individual message turn within a Novus conversation.
    Supports markdown, structured UI components, tool logs, and token auditing.
    """
    class Role(models.TextChoices):
        USER = 'user', 'Student'
        ASSISTANT = 'assistant', 'Novus'
        SYSTEM = 'system', 'System Instruction'
        TOOL = 'tool', 'Tool Result'

    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    content = models.TextField()
    structured_data = models.JSONField(
        blank=True,
        null=True,
        help_text="Structured card data for rich UI rendering (job cards, roadmap timeline, feedback, etc.)"
    )
    tool_calls = models.JSONField(
        blank=True,
        null=True,
        help_text="Records functions called by Gemini and their parameters"
    )
    tokens_used = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"[{self.get_role_display()}] in {self.conversation.id}: {self.content[:40]}..."


class StudentAIMemory(models.Model):
    """
    Long-term persistent memory for a student, completely student-inspectable and manageable.
    """
    class Category(models.TextChoices):
        PROFILE = 'PROFILE', 'Profile & Preferences'
        LEARNING = 'LEARNING', 'Learning & Progress'
        CAREER = 'CAREER', 'Career Goals & Targets'
        CONVERSATION = 'CONVERSATION', 'Key Insights & Decisions'

    student = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='ai_memories'
    )
    category = models.CharField(
        max_length=30,
        choices=Category.choices,
        default=Category.PROFILE
    )
    key = models.CharField(max_length=150)
    value = models.TextField()
    confidence = models.FloatField(default=1.0)
    is_active = models.BooleanField(default=True)
    source_conversation = models.ForeignKey(
        AIConversation,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='extracted_memories'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'key')
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.student.user.username} | {self.key}: {self.value[:35]}"


class MemoryUpdateLog(models.Model):
    """
    Audit log for memory creation, modification, toggling, or deletion.
    """
    class Action(models.TextChoices):
        CREATED = 'CREATED', 'Created'
        UPDATED = 'UPDATED', 'Updated'
        DELETED = 'DELETED', 'Deleted'
        TOGGLED = 'TOGGLED', 'Toggled'

    memory = models.ForeignKey(
        StudentAIMemory,
        on_delete=models.CASCADE,
        related_name='update_logs'
    )
    action = models.CharField(max_length=20, choices=Action.choices)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']


class StudentCareerGoal(models.Model):
    """
    Explicit career target and timeline recorded with VEX.
    """
    student = models.OneToOneField(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='career_goal'
    )
    target_role = models.CharField(max_length=150)
    target_industry = models.CharField(max_length=150, blank=True)
    target_companies = models.JSONField(default=list, blank=True)
    target_timeline = models.CharField(max_length=100, blank=True, default='6 Months')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.user.username} -> {self.target_role}"


class StudentLearningPlan(models.Model):
    """
    Personalized structured roadmap generated by VEX for a student.
    """
    student = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='learning_plans'
    )
    title = models.CharField(max_length=200)
    target_role = models.CharField(max_length=150)
    duration_weeks = models.PositiveIntegerField(default=12)
    phases = models.JSONField(default=list, help_text="Weekly phases, focus areas, project objectives")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.student.user.username})"


class LearningPlanProgress(models.Model):
    """
    Tracks completed milestones within a learning plan.
    """
    plan = models.ForeignKey(
        StudentLearningPlan,
        on_delete=models.CASCADE,
        related_name='progress_items'
    )
    phase_index = models.PositiveIntegerField(default=0)
    task_key = models.CharField(max_length=120)
    task_title = models.CharField(max_length=255)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('plan', 'task_key')

    def __str__(self):
        status = 'Done' if self.is_completed else 'Pending'
        return f"[{status}] {self.task_title}"


class InterviewSession(models.Model):
    """
    Interactive mock interview session with VEX.
    """
    class InterviewType(models.TextChoices):
        TECHNICAL = 'TECHNICAL', 'Technical & System Architecture'
        HR = 'HR', 'HR & Culture Fit'
        CODING = 'CODING', 'Coding & DSA Discussion'
        BEHAVIORAL = 'BEHAVIORAL', 'Behavioral (STAR Method)'
        PROJECT = 'PROJECT', 'Deep-dive Project Defense'

    class Status(models.TextChoices):
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        COMPLETED = 'COMPLETED', 'Completed'
        ABANDONED = 'ABANDONED', 'Abandoned'

    student = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='mock_interviews'
    )
    target_role = models.CharField(max_length=150)
    interview_type = models.CharField(
        max_length=30,
        choices=InterviewType.choices,
        default=InterviewType.TECHNICAL
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS
    )
    overall_feedback = models.TextField(blank=True)
    rubric_scores = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.user.username} - {self.get_interview_type_display()} ({self.target_role})"


class InterviewQuestion(models.Model):
    """
    Individual question, student answer, and rubric feedback within a mock interview.
    """
    session = models.ForeignKey(
        InterviewSession,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    order = models.PositiveIntegerField(default=1)
    question_text = models.TextField()
    student_response = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    model_answer = models.TextField(blank=True)
    score = models.PositiveIntegerField(default=0, help_text="Rating out of 10")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']


class ResumeAnalysis(models.Model):
    """
    Structured resume feedback, gap analysis, and tailored recommendations.
    """
    student = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='resume_analyses'
    )
    resume = models.ForeignKey(
        'students.Resume',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='vex_analyses'
    )
    target_role = models.CharField(max_length=150)
    strengths = models.JSONField(default=list)
    gaps = models.JSONField(default=list)
    improvements = models.JSONField(default=list)
    suggested_summary = models.TextField(blank=True)
    keyword_recommendations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class AIMessageFeedback(models.Model):
    """
    User thumbs up/down feedback on VEX message responses.
    """
    message = models.OneToOneField(
        AIMessage,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    is_helpful = models.BooleanField()
    feedback_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AIUsageLog(models.Model):
    """
    Token and quota usage monitoring per student.
    """
    student = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='ai_usage_logs'
    )
    prompt_tokens = models.PositiveIntegerField(default=0)
    candidate_tokens = models.PositiveIntegerField(default=0)
    model_name = models.CharField(max_length=100)
    action_type = models.CharField(max_length=50, default='chat')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

