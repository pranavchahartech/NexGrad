"""
Explainable Career Intelligence Services for Nexgrad.
Calculates weighted match affinity and diagnoses skill gaps.
"""

def calculate_opportunity_match(student_profile, job):
    """
    Computes an explainable compatibility match score between a student profile and a job listing.
    
    Formula:
    Match Score = (Skill Match * 0.40) +
                  (Academic Eligibility * 0.25) +
                  (Branch Alignment * 0.15) +
                  (Project Evidence * 0.10) +
                  (Location Preference * 0.10)
    """
    reasons = []
    missing_skills = []

    # 1. Skill Match (40%)
    job_skills = set(job.required_skills.values_list('name', flat=True))
    student_skills = set(student_profile.skills.values_list('skill_name', flat=True))

    if job_skills:
        matched_skills = job_skills.intersection(student_skills)
        missing_skills = list(job_skills.difference(student_skills))
        skill_score = (len(matched_skills) / len(job_skills)) * 100
        if matched_skills:
            reasons.append(f"Demonstrated proficiency in: {', '.join(matched_skills)}")
    else:
        skill_score = 80
        matched_skills = set()

    # 2. Academic Cutoff (25%)
    has_student_cgpa = student_profile.cgpa is not None
    job_min_cgpa = getattr(job, 'min_cgpa', None)
    has_min_cgpa = job_min_cgpa is not None and job_min_cgpa > 0

    if not has_min_cgpa:
        eligibility_score = 100
        reasons.append("No minimum CGPA requirement for this position")
    elif has_student_cgpa:
        if student_profile.cgpa >= job_min_cgpa:
            eligibility_score = 100
            reasons.append(f"CGPA ({student_profile.cgpa}) satisfies the minimum threshold ({job_min_cgpa})")
        else:
            eligibility_score = 40
            missing_skills.append(f"CGPA ({student_profile.cgpa}) is below the required threshold ({job_min_cgpa})")
    else:
        eligibility_score = 50
        reasons.append(f"Minimum CGPA of {job_min_cgpa} required (profile CGPA not yet specified)")

    # 3. Branch Alignment (15%)
    if job.eligible_branches:
        eligible_branches = [b.strip().upper() for b in job.eligible_branches.split(',') if b.strip()]
    else:
        eligible_branches = []

    student_branch = (student_profile.branch or '').strip().upper()
    if not eligible_branches:
        branch_score = 100
        reasons.append("All engineering disciplines are eligible")
    elif student_branch and student_branch in eligible_branches:
        branch_score = 100
        branch_display = student_profile.get_branch_display() if hasattr(student_profile, 'get_branch_display') else student_profile.branch
        reasons.append(f"Branch ({branch_display}) matches eligible departments")
    else:
        branch_score = 60
        if not student_branch:
            reasons.append("Academic branch not yet specified in profile")
        else:
            branch_display = student_profile.get_branch_display() if hasattr(student_profile, 'get_branch_display') else student_profile.branch
            reasons.append(f"Eligible departments: {', '.join(eligible_branches)} (current: {branch_display})")

    # 4. Project Evidence (10%)
    project_count = student_profile.projects.count()
    project_score = min(project_count * 50, 100)
    if project_count > 0:
        reasons.append(f"{project_count} verified engineering project(s) showcased in portfolio")

    # 5. Location / Work preference (10%)
    location_score = 90

    total_score = round(
        (skill_score * 0.40) +
        (eligibility_score * 0.25) +
        (branch_score * 0.15) +
        (project_score * 0.10) +
        (location_score * 0.10)
    )

    return {
        'score': total_score,
        'matched_skills': list(matched_skills),
        'missing_skills': missing_skills,
        'reasons': reasons,
        'is_strong_match': total_score >= 75,
    }

