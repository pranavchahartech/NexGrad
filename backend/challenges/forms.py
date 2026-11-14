from django import forms
from django.utils import timezone
from .models import Challenge, ChallengeAttachment, ChallengeAssignment, ChallengeSubmission, ChallengeEvaluation
from applications.models import Application

class ChallengeForm(forms.ModelForm):
    """
    Recruiter form to author and configure private candidate challenges.
    """
    class Meta:
        model = Challenge
        fields = [
            'title', 'job', 'challenge_type', 'difficulty',
            'description', 'problem_statement', 'instructions', 'technical_requirements',
            'required_skills', 'input_output_specs', 'reference_materials',
            'maximum_marks', 'start_at', 'deadline', 'time_limit_minutes',
            'allowed_submission_formats', 'max_file_size_mb', 'allow_resubmission',
            'status'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Django REST API & Celery Task Pipeline'}),
            'job': forms.Select(attrs={'class': 'form-select'}),
            'challenge_type': forms.Select(attrs={'class': 'form-select'}),
            'difficulty': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief overview and context for the candidate...'}),
            'problem_statement': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Detailed problem specifications, constraints, and requirements...'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Submission guidelines, environment setup, and deliverable instructions...'}),
            'technical_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'e.g. Python 3.12, Django 5, PostgreSQL, pytest, Docker...'}),
            'required_skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, REST APIs, PostgreSQL, Docker'}),
            'input_output_specs': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Sample payloads, input schemas, or expected outputs...'}),
            'reference_materials': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Links to APIs, GitHub boilerplates, or documentation...'}),
            'maximum_marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 10, 'max': 500}),
            'start_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'deadline': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'time_limit_minutes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional (e.g. 180 for 3 hours)'}),
            'allowed_submission_formats': forms.TextInput(attrs={'class': 'form-control'}),
            'max_file_size_mb': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100}),
            'allow_resubmission': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, recruiter_profile=None, **kwargs):
        super().__init__(*args, **kwargs)
        if recruiter_profile:
            # Only allow selecting jobs posted by this recruiter's company
            self.fields['job'].queryset = recruiter_profile.posted_jobs.filter(is_active=True)
            self.fields['job'].required = False
            self.fields['job'].empty_label = "-- Link to Vacancy (Recommended) --"

    def clean(self):
        cleaned_data = super().clean()
        start_at = cleaned_data.get('start_at')
        deadline = cleaned_data.get('deadline')
        if start_at and deadline and deadline <= start_at:
            self.add_error('deadline', "Submission deadline must be later than the challenge start date/time.")
        return cleaned_data


class ChallengeAttachmentForm(forms.ModelForm):
    class Meta:
        model = ChallengeAttachment
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Starter Code / Architecture Diagram'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ChallengeSubmissionForm(forms.ModelForm):
    """
    Student solution submission form with file upload, git URL, demo link, and verification.
    """
    class Meta:
        model = ChallengeSubmission
        fields = [
            'description', 'uploaded_file', 'repository_url',
            'demonstration_url', 'supporting_document', 'additional_comments'
        ]
        widgets = {
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Provide an overview of your implementation, architecture decisions, trade-offs, and instructions for running your code...'
            }),
            'uploaded_file': forms.FileInput(attrs={'class': 'form-control'}),
            'repository_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/your-username/your-repository'}),
            'demonstration_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://your-demo-deployment.app'}),
            'supporting_document': forms.FileInput(attrs={'class': 'form-control'}),
            'additional_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional notes or considerations for the evaluation team...'}),
        }

    def clean_uploaded_file(self):
        file = self.cleaned_data.get('uploaded_file')
        if file:
            max_size_mb = 25
            if file.size > max_size_mb * 1024 * 1024:
                raise forms.ValidationError(f"File size exceeds the {max_size_mb}MB limit.")
            # Disallow executable binary files for security
            disallowed_extensions = ['.exe', '.bat', '.sh', '.com', '.msi', '.vbs', '.cmd']
            for ext in disallowed_extensions:
                if file.name.lower().endswith(ext):
                    raise forms.ValidationError(f"File format '{ext}' is strictly not permitted for security reasons.")
        return file

    def clean(self):
        cleaned_data = super().clean()
        desc = cleaned_data.get('description', '').strip()
        file = cleaned_data.get('uploaded_file')
        repo = cleaned_data.get('repository_url', '').strip()
        demo = cleaned_data.get('demonstration_url', '').strip()

        if not desc and not file and not repo and not demo:
            raise forms.ValidationError("Please provide at least a solution description, source code upload, or repository link.")
        return cleaned_data


class ChallengeEvaluationForm(forms.ModelForm):
    """
    Recruiter evaluation form with multi-criteria rubric scoring and candidate feedback.
    """
    class Meta:
        model = ChallengeEvaluation
        fields = [
            'technical_correctness', 'code_quality', 'problem_solving',
            'practical_implementation', 'documentation',
            'feedback', 'strengths', 'areas_for_improvement',
            'internal_recruiter_notes', 'recommended_stage', 'evaluation_status'
        ]
        widgets = {
            'technical_correctness': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'code_quality': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'problem_solving': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'practical_implementation': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'documentation': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed evaluation summary and constructive review visible to candidate...'}),
            'strengths': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Highlights and key strengths observed in the submission...'}),
            'areas_for_improvement': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Key areas where the candidate can improve...'}),
            'internal_recruiter_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Internal notes (private to your hiring team, never visible to student)...'}),
            'recommended_stage': forms.Select(attrs={'class': 'form-select'}),
            'evaluation_status': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tc = cleaned_data.get('technical_correctness') or 0
        cq = cleaned_data.get('code_quality') or 0
        ps = cleaned_data.get('problem_solving') or 0
        pi = cleaned_data.get('practical_implementation') or 0
        doc = cleaned_data.get('documentation') or 0
        total = tc + cq + ps + pi + doc
        self.instance.total_marks = total
        return cleaned_data

