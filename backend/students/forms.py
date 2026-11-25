from django import forms
from .models import StudentProfile
from institutions.models import Institution

class StudentProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    phone = forms.CharField(
        max_length=25,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+91 98765 43210'
        })
    )

    class Meta:
        model = StudentProfile
        fields = [
            'profile_picture',
            'phone',
            'address',
            'location',
            'college_name',
            'institution',
            'degree',
            'branch',
            'graduation_year',
            'cgpa',
            'school_name',
            'school_marks',
            'tenth_marks',
            'twelfth_marks',
            'headline',
            'bio',
            'github_url',
            'linkedin_url',
            'portfolio_url',
        ]
        widgets = {
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Current residential or campus address'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'City, State (e.g. Bengaluru, Karnataka)'
            }),
            'college_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Lovely Professional University / NIT Trichy'
            }),
            'institution': forms.Select(attrs={
                'class': 'form-select'
            }),
            'degree': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. B.Tech, BCA, MCA, B.Sc, M.Tech'
            }),
            'branch': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Computer Science & Engineering, AI & DS'
            }),
            'graduation_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 2026',
                'min': 2000,
                'max': 2040
            }),
            'cgpa': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 8.75',
                'step': '0.01',
                'min': '0',
                'max': '10'
            }),
            'school_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Delhi Public School / St. Xavier High School'
            }),
            'school_marks': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 92% or 9.4 CGPA'
            }),
            'tenth_marks': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 94.5% / 10 CGPA'
            }),
            'twelfth_marks': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 91.2% (PCM)'
            }),
            'headline': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Aspiring Full-Stack Software Engineer | Cloud Enthusiast'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Tell recruiters about your engineering journey, interests, and aspirations...'
            }),
            'github_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/yourusername'
            }),
            'linkedin_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/yourusername'
            }),
            'portfolio_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://yourportfolio.dev'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            if not self.initial.get('phone'):
                self.fields['phone'].initial = getattr(user, 'phone', '')


class ProjectForm(forms.ModelForm):
    class Meta:
        from .models import Project
        model = Project
        fields = ['title', 'technologies', 'description', 'repo_url', 'live_url']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Project Title (e.g. Distributed Task Queue)'}),
            'technologies': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, Redis, Docker, FastAPI'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Summary of features, architecture, and impact...'}),
            'repo_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/username/project'}),
            'live_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://project-demo.live (optional)'}),
        }


class SkillForm(forms.ModelForm):
    class Meta:
        from .models import StudentSkill
        model = StudentSkill
        fields = ['skill_name', 'proficiency']
        widgets = {
            'skill_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Python, React, PostgreSQL, Docker'}),
            'proficiency': forms.Select(attrs={'class': 'form-select'}),
        }


