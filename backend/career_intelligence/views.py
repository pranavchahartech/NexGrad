from django.shortcuts import render, get_object_or_404
from .models import CareerRoadmap

def roadmap_detail(request, target_role):
    roadmap = get_object_or_404(CareerRoadmap, slug=target_role)
    milestones = roadmap.milestones.all()
    return render(request, 'core/roadmap_detail.html', {
        'roadmap': roadmap,
        'milestones': milestones,
    })

