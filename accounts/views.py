from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile
from .permissions import admin_required, manager_required

@login_required
def profile(request):
    """User profile view"""
    context = {
        'user': request.user,
        'profile': request.user.profile if hasattr(request.user, 'profile') else None,
    }
    return render(request, 'accounts/profile.html', context)

@admin_required
def user_list(request):
    """List all users (admin only)"""
    users = User.objects.select_related('profile').all()
    
    context = {
        'users': users,
    }
    return render(request, 'accounts/user_list.html', context)

@admin_required
def user_create(request):
    """Create new user (admin only)"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        role = request.POST.get('role', 'CASHIER')
        phone = request.POST.get('phone', '')
        
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return redirect('user_create')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return redirect('user_create')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('user_create')
        
        user = User.objects.create_user(
            username=username,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = role
        profile.phone = phone
        profile.save()
        
        messages.success(request, f'User "{username}" created successfully with role: {profile.get_role_display()}.')
        return redirect('user_list')
    
    return render(request, 'accounts/user_form.html')

@admin_required
def user_update(request, pk):
    """Update user (admin only)"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()
        
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.role = request.POST.get('role', profile.role)
        profile.phone = request.POST.get('phone', profile.phone)
        profile.save()
        
        messages.success(request, f'User "{user.username}" updated.')
        return redirect('user_list')
    
    return render(request, 'accounts/user_form.html', {'edit_user': user})

@admin_required
def user_delete(request, pk):
    """Delete user (admin only)"""
    user = get_object_or_404(User, pk=pk)
    
    if user == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('user_list')
    
    if request.method == 'POST':
        user.delete()
        messages.success(request, f'User "{user.username}" deleted.')
        return redirect('user_list')
    
    return render(request, 'accounts/user_confirm_delete.html', {'edit_user': user})

@admin_required
def user_reset_password(request, pk):
    """Reset user password (admin only)"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        if new_password:
            user.set_password(new_password)
            user.save()
            messages.success(request, f'Password reset for "{user.username}".')
            return redirect('user_list')
    
    return render(request, 'accounts/user_reset_password.html', {'edit_user': user})
