"""
Authentication views for login and signup.
"""
import logging
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages

from apps.companies.models import Company

logger = logging.getLogger(__name__)


def login_view(request):
    """Handle user login."""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard:index')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')


def signup_view(request):
    """Handle user registration."""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        company_name = request.POST.get('company_name')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        errors = {}
        
        if User.objects.filter(username=username).exists():
            errors['username'] = ['Username already exists.']
        
        if User.objects.filter(email=email).exists():
            errors['email'] = ['Email already registered.']
        
        if password1 != password2:
            errors['password2'] = ['Passwords do not match.']
        
        if len(password1) < 8:
            errors['password1'] = ['Password must be at least 8 characters.']
        
        if errors:
            return render(request, 'auth/signup.html', {
                'form': {'errors': errors, **request.POST}
            })
        
        # Create user and company
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            
            # Create company for this user
            company = Company.objects.create(
                name=company_name,
                owner=user,
            )
            
            # Log the user in
            login(request, user)
            
            logger.info(f"New user registered: {username}, Company: {company_name}")
            messages.success(request, 'Account created successfully!')
            
            return redirect('dashboard:index')
            
        except Exception as e:
            logger.error(f"Error creating user/company: {e}")
            messages.error(request, 'An error occurred. Please try again.')
            return render(request, 'auth/signup.html', {'form': request.POST})
    
    return render(request, 'auth/signup.html')
