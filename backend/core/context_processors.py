def brand_context(request):
    """
    Global context processor making Nexgrad brand tokens and profile status available in all templates.
    """
    context = {
        'BRAND_NAME': 'Nexgrad',
        'BRAND_TAGLINE': 'The Engineering Career Intelligence & Opportunity Platform',
        'BRAND_COLORS': {
            'NAVY': '#082B4C',
            'CREAM': '#F3EBDD',
            'SAGE': '#B9BEAA',
            'TEAL': '#96AAA5',
            'SLATE': '#426F87',
        },
        'user_has_resume': False,
        'show_global_resume_prompt': False,
    }

    if request.user.is_authenticated and getattr(request.user, 'is_student', False):
        try:
            profile = getattr(request.user, 'student_profile', None)
            if profile:
                has_cv = profile.resumes.exists()
                context['user_has_resume'] = has_cv
                context['show_global_resume_prompt'] = (not has_cv) and (not request.session.get('skip_resume_prompt', False))
        except Exception:
            pass

    return context


