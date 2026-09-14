from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from functools import wraps
from django.shortcuts import redirect

def admin_required(view_func):
    """Require admin role or superuser"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        # Allow superusers
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        # Check profile
        if not hasattr(request.user, 'profile'):
            raise PermissionDenied
        if request.user.profile.role == 'ADMIN':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

def manager_required(view_func):
    """Require manager or admin role"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        # Allow superusers
        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        # Check profile
        if not hasattr(request.user, 'profile'):
            raise PermissionDenied
        if request.user.profile.role in ['ADMIN', 'MANAGER']:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return _wrapped_view

def cashier_required(view_func):
    """Require any authenticated user with profile"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
