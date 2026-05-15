"""
===========================================
Users App — Web Views (Template-based)
===========================================
Server-rendered views for login, logout, and dashboard access.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import ActivityLog


def home_view(request):
    """Site root: send logged-in users to dashboard, others to login."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('login')


def login_view(request):
    """
    GET  /auth/login/ — Render login page
    POST /auth/login/ — Authenticate and redirect to dashboard
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # Check if account is locked
        from .models import CustomUser
        try:
            user_check = CustomUser.objects.get(email=email)
            if user_check.is_locked:
                messages.error(request, 'Account is locked due to too many failed attempts. Contact administrator.')
                return render(request, 'auth/login.html')
        except CustomUser.DoesNotExist:
            pass

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'auth/login.html')


def logout_view(request):
    """Log out and redirect to login page."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


@login_required
def profile_view(request):
    """User profile page."""
    return render(request, 'auth/profile.html', {'user': request.user})
