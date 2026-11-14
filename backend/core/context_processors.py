def brand_context(request):
    """
    Global context processor making Nexgrad brand tokens available in all templates.
    """
    return {
        'BRAND_NAME': 'Nexgrad',
        'BRAND_TAGLINE': 'The Engineering Career Intelligence & Opportunity Platform',
        'BRAND_COLORS': {
            'NAVY': '#082B4C',
            'CREAM': '#F3EBDD',
            'SAGE': '#B9BEAA',
            'TEAL': '#96AAA5',
            'SLATE': '#426F87',
        }
    }

