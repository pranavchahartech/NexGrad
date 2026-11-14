from django.urls import path
from . import recruiter_views, student_views

app_name = 'challenges'

urlpatterns = [
    # =========================================================================
    # RECRUITER CHALLENGE MANAGEMENT ROUTES
    # =========================================================================
    path('recruiter/', recruiter_views.recruiter_challenge_list),
    path('recruiter/challenges/', recruiter_views.recruiter_challenge_list, name='recruiter_challenge_list'),
    path('recruiter/challenges/create/', recruiter_views.recruiter_challenge_create, name='recruiter_challenge_create'),
    path('recruiter/challenges/<int:challenge_id>/', recruiter_views.recruiter_challenge_detail, name='recruiter_challenge_detail'),
    path('recruiter/challenges/<int:challenge_id>/edit/', recruiter_views.recruiter_challenge_edit, name='recruiter_challenge_edit'),
    path('recruiter/challenges/<int:challenge_id>/assign/', recruiter_views.recruiter_challenge_assign, name='recruiter_challenge_assign'),
    path('recruiter/challenges/<int:challenge_id>/submissions/', recruiter_views.recruiter_challenge_submissions, name='recruiter_challenge_submissions'),
    path('recruiter/submissions/<int:submission_id>/evaluate/', recruiter_views.recruiter_submission_evaluate, name='recruiter_submission_evaluate'),
    path('recruiter/assignments/<int:assignment_id>/revoke/', recruiter_views.recruiter_assignment_revoke, name='recruiter_assignment_revoke'),

    # =========================================================================
    # STUDENT CHALLENGE ACCESS & SUBMISSION ROUTES
    # =========================================================================
    path('my-challenges/', student_views.student_my_challenges),
    path('student/my-challenges/', student_views.student_my_challenges, name='student_my_challenges'),
    path('student/challenges/<int:assignment_id>/', student_views.student_challenge_detail, name='student_challenge_detail'),
    path('student/challenges/<int:assignment_id>/start/', student_views.student_challenge_start, name='student_challenge_start'),
    path('student/challenges/<int:assignment_id>/submit/', student_views.student_challenge_submit, name='student_challenge_submit'),
    path('student/submissions/<int:submission_id>/', student_views.student_submission_detail, name='student_submission_detail'),
    path('student/challenges/<int:assignment_id>/feedback/', student_views.student_challenge_feedback, name='student_challenge_feedback'),
]

