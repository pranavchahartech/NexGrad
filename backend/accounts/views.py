from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import StudentRegistrationForm, RecruiterRegistrationForm, LoginForm
from .models import CustomUser

def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            if user.role == CustomUser.Role.STUDENT:
                return redirect('students:dashboard')
            elif user.role == CustomUser.Role.RECRUITER:
                return redirect('recruiters:dashboard')
            elif user.role == CustomUser.Role.INSTITUTION:
                return redirect('institutions:dashboard')
            return redirect('core:home')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been successfully logged out.")
    return redirect('core:home')

def register_student(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            from students.models import StudentProfile
            StudentProfile.objects.get_or_create(user=user)
            login(request, user)
            request.session['is_new_user'] = True
            request.session['just_registered'] = True
            messages.success(request, f"Welcome to Nexgrad, {user.first_name or user.username}! Your student account has been created.")
            return redirect('students:dashboard')
        else:
            messages.error(request, "Please correct the errors below to register.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'accounts/register_student.html', {'form': form})

def register_recruiter(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = RecruiterRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Your recruiter account has been created successfully!")
            return redirect('recruiters:dashboard')
        else:
            messages.error(request, "Please correct the errors below to register.")
    else:
        form = RecruiterRegistrationForm()

    return render(request, 'accounts/register_recruiter.html', {'form': form})

