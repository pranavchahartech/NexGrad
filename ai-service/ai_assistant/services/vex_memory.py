import re
from typing import List, Optional
from django.utils import timezone
from students.models import StudentProfile
from ai_assistant.models import StudentAIMemory, MemoryUpdateLog, AIConversation


class VEXMemoryService:
    """
    Manages student-controlled persistent memory for VEX.
    Ensures strict student-level isolation and auditable changes.
    """

    @classmethod
    def get_student_memories(cls, student: StudentProfile, include_inactive: bool = False) -> List[StudentAIMemory]:
        """
        Retrieves all memories belonging to the authenticated student.
        """
        qs = StudentAIMemory.objects.filter(student=student)
        if not include_inactive:
            qs = qs.filter(is_active=True)
        return list(qs.order_by('category', '-updated_at'))

    @classmethod
    def save_or_update_memory(
        cls,
        student: StudentProfile,
        category: str,
        key: str,
        value: str,
        confidence: float = 1.0,
        conversation: Optional[AIConversation] = None
    ) -> StudentAIMemory:
        """
        Saves or updates a student memory key-value pair and logs the action.
        """
        key_clean = key.strip()[:150]
        value_clean = value.strip()

        # Sanitize sensitive patterns
        if any(w in key_clean.lower() or w in value_clean.lower() for w in ['password', 'secret', 'token', 'auth']):
            return None

        memory, created = StudentAIMemory.objects.get_or_create(
            student=student,
            key=key_clean,
            defaults={
                'category': category,
                'value': value_clean,
                'confidence': confidence,
                'source_conversation': conversation,
                'is_active': True,
            }
        )

        if not created:
            old_value = memory.value
            if old_value != value_clean:
                memory.value = value_clean
                memory.category = category
                memory.confidence = confidence
                if conversation:
                    memory.source_conversation = conversation
                memory.is_active = True
                memory.save()

                MemoryUpdateLog.objects.create(
                    memory=memory,
                    action=MemoryUpdateLog.Action.UPDATED,
                    old_value=old_value,
                    new_value=value_clean
                )
        else:
            MemoryUpdateLog.objects.create(
                memory=memory,
                action=MemoryUpdateLog.Action.CREATED,
                old_value='',
                new_value=value_clean
            )

        return memory

    @classmethod
    def toggle_memory(cls, student: StudentProfile, memory_id: int) -> Optional[StudentAIMemory]:
        """
        Toggles is_active on a student's memory item.
        """
        try:
            memory = StudentAIMemory.objects.get(id=memory_id, student=student)
            memory.is_active = not memory.is_active
            memory.save(update_fields=['is_active', 'updated_at'])

            MemoryUpdateLog.objects.create(
                memory=memory,
                action=MemoryUpdateLog.Action.TOGGLED,
                old_value=str(not memory.is_active),
                new_value=str(memory.is_active)
            )
            return memory
        except StudentAIMemory.DoesNotExist:
            return None

    @classmethod
    def delete_memory(cls, student: StudentProfile, memory_id: int) -> bool:
        """
        Deletes a student memory permanently.
        """
        try:
            memory = StudentAIMemory.objects.get(id=memory_id, student=student)
            MemoryUpdateLog.objects.create(
                memory=memory,
                action=MemoryUpdateLog.Action.DELETED,
                old_value=memory.value,
                new_value='[DELETED]'
            )
            memory.delete()
            return True
        except StudentAIMemory.DoesNotExist:
            return False

    @classmethod
    def extract_memories_from_text(
        cls,
        student: StudentProfile,
        user_message: str,
        assistant_message: str,
        conversation: Optional[AIConversation] = None
    ) -> List[StudentAIMemory]:
        """
        Analyzes conversation turns for student declarations regarding career goals,
        preferred tools, target companies, or learning hurdles.
        """
        extracted = []
        msg_lower = user_message.lower()

        # Target role patterns
        role_matches = re.findall(
            r'(?:i want to become|aiming for|targeting|preparing for|my dream role is|as a)\s+(?:an?\s+)?([a-z\s]{3,35}?)(?:\.|\,|$|\b(?:role|engineer|developer|architect|specialist|position)\b)',
            msg_lower
        )
        for r in role_matches:
            role = r.strip().title()
            if len(role) > 3 and not any(w in role.lower() for w in ['job', 'internship', 'interview', 'question', 'problem']):
                mem = cls.save_or_update_memory(
                    student=student,
                    category=StudentAIMemory.Category.CAREER,
                    key="Target Role",
                    value=role,
                    confidence=0.9,
                    conversation=conversation
                )
                if mem:
                    extracted.append(mem)

        # Target company patterns
        company_matches = re.findall(
            r'(?:want to work at|apply to|targeting|interested in)\s+([a-zA-Z0-9\s]{2,25}?)(?:\b(?:company|office|team|interview)\b|\.|\,|$)',
            user_message
        )
        for c in company_matches:
            comp = c.strip()
            if comp and comp.lower() not in ['a', 'the', 'any', 'good', 'some', 'my', 'this']:
                mem = cls.save_or_update_memory(
                    student=student,
                    category=StudentAIMemory.Category.CAREER,
                    key="Target Company Preference",
                    value=comp,
                    confidence=0.85,
                    conversation=conversation
                )
                if mem:
                    extracted.append(mem)

        # Preferred stack / languages
        stack_matches = re.findall(
            r'(?:prefer|working with|proficient in|learning|love)\s+([a-zA-Z\+\#\.\s]{2,20}?)(?:\b(?:for backend|for frontend|stack|language|framework)\b|\.|\,|$)',
            user_message
        )
        for s in stack_matches:
            tech = s.strip()
            if tech and len(tech) >= 2 and tech.lower() not in ['a', 'the', 'to', 'it', 'my', 'some']:
                mem = cls.save_or_update_memory(
                    student=student,
                    category=StudentAIMemory.Category.PROFILE,
                    key=f"Preferred Technology: {tech.title()}",
                    value=f"Student expressed strong preference/active learning in {tech.title()}",
                    confidence=0.8,
                    conversation=conversation
                )
                if mem:
                    extracted.append(mem)

        # Learning weaknesses or needs
        weak_matches = re.findall(
            r'(?:struggle with|weak at|need to improve|find.*difficult|confused about)\s+([a-zA-Z0-9\s]{3,30}?)(?:\.|\,|$)',
            msg_lower
        )
        for w in weak_matches:
            topic = w.strip().title()
            if topic and len(topic) >= 3:
                mem = cls.save_or_update_memory(
                    student=student,
                    category=StudentAIMemory.Category.LEARNING,
                    key=f"Focus Area: {topic}",
                    value=f"Needs practice and guidance in {topic}",
                    confidence=0.85,
                    conversation=conversation
                )
                if mem:
                    extracted.append(mem)

        return extracted

