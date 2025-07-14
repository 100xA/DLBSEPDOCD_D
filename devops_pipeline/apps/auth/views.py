"""Auth views."""

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

from .models import UserSession


def login_view(request):
    """Enhanced login view with session tracking."""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Track session for security monitoring
            UserSession.objects.create(
                user=user,
                session_key=request.session.session_key,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'status': 'success', 'user': user.username})
            return redirect('catalog:product_list')
        else:
            if request.headers.get('Accept') == 'application/json':
                return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=401)
            return render(request, 'registration/login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'registration/login.html')


@login_required
def logout_view(request):
    """Enhanced logout view with session cleanup."""
    # Mark session as inactive
    try:
        session = UserSession.objects.get(
            user=request.user,
            session_key=request.session.session_key,
            is_active=True
        )
        session.is_active = False
        session.save()
    except UserSession.DoesNotExist:
        pass
    
    logout(request)
    return redirect('catalog:product_list')


@csrf_exempt
@require_http_methods(["POST"])
def check_session(request):
    """API endpoint to check session validity."""
    if not request.user.is_authenticated:
        return JsonResponse({'valid': False}, status=401)
    
    try:
        session = UserSession.objects.get(
            user=request.user,
            session_key=request.session.session_key,
            is_active=True
        )
        return JsonResponse({
            'valid': True,
            'user': request.user.username,
            'last_activity': session.last_activity.isoformat()
        })
    except UserSession.DoesNotExist:
        return JsonResponse({'valid': False}, status=401)


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip 