import requests
import secrets
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from .models import User
from .auth_utils import (
    generate_access_token, 
    generate_refresh_token,
    verify_refresh_token,
    revoke_refresh_token,
    generate_pkce_challenge
)


# Store PKCE challenges temporarily (in production, use Redis)
pkce_store = {}


@require_http_methods(["GET"])
def github_login(request):
    """Initiate GitHub OAuth flow"""
    
    # Get parameters from request
    code_challenge = request.GET.get('code_challenge')
    state = request.GET.get('state')
    redirect_uri = request.GET.get('redirect_uri', f"{settings.BACKEND_URL}/auth/github/callback")
    
    # Store code_challenge with state for verification
    if code_challenge and state:
        pkce_store[state] = code_challenge
    
    # Build GitHub OAuth URL
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope=user:email"
        f"&state={state or secrets.token_urlsafe(32)}"
    )
    
    return HttpResponseRedirect(github_auth_url)


@require_http_methods(["GET"])
def github_callback(request):
    """Handle GitHub OAuth callback"""
    
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    if not code:
        return JsonResponse({
            'status': 'error',
            'message': 'Authorization code missing'
        }, status=400)
    
    # Exchange code for access token
    token_response = requests.post(
        'https://github.com/login/oauth/access_token',
        headers={'Accept': 'application/json'},
        data={
            'client_id': settings.GITHUB_CLIENT_ID,
            'client_secret': settings.GITHUB_CLIENT_SECRET,
            'code': code,
        }
    )
    
    token_data = token_response.json()
    github_access_token = token_data.get('access_token')
    
    if not github_access_token:
        return JsonResponse({
            'status': 'error',
            'message': 'Failed to obtain access token from GitHub'
        }, status=400)
    
    # Get user info from GitHub
    user_response = requests.get(
        'https://api.github.com/user',
        headers={'Authorization': f'Bearer {github_access_token}'}
    )
    
    github_user = user_response.json()
    
    # Get email if not in primary response
    if not github_user.get('email'):
        email_response = requests.get(
            'https://api.github.com/user/emails',
            headers={'Authorization': f'Bearer {github_access_token}'}
        )
        emails = email_response.json()
        primary_email = next((e['email'] for e in emails if e['primary']), None)
        github_user['email'] = primary_email
    
    # Create or update user
    user, created = User.objects.update_or_create(
        github_id=str(github_user['id']),
        defaults={
            'username': github_user['login'],
            'email': github_user.get('email'),
            'avatar_url': github_user.get('avatar_url'),
            'last_login_at': timezone.now()
        }
    )
    
    # Generate tokens
    access_token = generate_access_token(user)
    refresh_token = generate_refresh_token(user)
    
    # If this is a CLI request (with code_verifier in session), return JSON
    # Otherwise, redirect to frontend
    cli_request = request.GET.get('cli', 'false') == 'true'
    
    if cli_request:
        return JsonResponse({
            'status': 'success',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'avatar_url': user.avatar_url
            }
        })
    
    # For web, redirect to frontend with tokens
    frontend_url = settings.FRONTEND_URL
    redirect_url = f"{frontend_url}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
    
    return HttpResponseRedirect(redirect_url)


@csrf_exempt
@require_http_methods(["POST"])
def refresh_token_view(request):
    """Refresh access token using refresh token"""
    
    import json
    data = json.loads(request.body)
    
    refresh_token = data.get('refresh_token')
    
    if not refresh_token:
        return JsonResponse({
            'status': 'error',
            'message': 'Refresh token required'
        }, status=400)
    
    # Verify refresh token
    token_obj = verify_refresh_token(refresh_token)
    
    if not token_obj:
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid or expired refresh token'
        }, status=401)
    
    # Revoke old refresh token
    token_obj.is_revoked = True
    token_obj.save()
    
    # Generate new tokens
    user = token_obj.user
    new_access_token = generate_access_token(user)
    new_refresh_token = generate_refresh_token(user)
    
    return JsonResponse({
        'status': 'success',
        'access_token': new_access_token,
        'refresh_token': new_refresh_token
    })


@csrf_exempt
@require_http_methods(["POST"])
def logout_view(request):
    """Logout user and revoke refresh token"""
    
    import json
    
    try:
        data = json.loads(request.body)
        refresh_token = data.get('refresh_token')
        
        if refresh_token:
            revoke_refresh_token(refresh_token)
    except:
        pass
    
    return JsonResponse({
        'status': 'success',
        'message': 'Logged out successfully'
    })