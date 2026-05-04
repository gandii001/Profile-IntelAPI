import jwt
import secrets
from datetime import datetime, timedelta
from django.conf import settings
from .models import User, RefreshToken


def generate_access_token(user):
    """Generate JWT access token (3 minutes expiry)"""
    payload = {
        'user_id': str(user.id),
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(minutes=3),
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def generate_refresh_token(user):
    """Generate and store refresh token (5 minutes expiry)"""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    
    RefreshToken.objects.create(
        user=user,
        token=token,
        expires_at=expires_at
    )
    
    return token


def verify_access_token(token):
    """Verify and decode access token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        if payload.get('type') != 'access':
            return None
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def verify_refresh_token(token):
    """Verify refresh token from database"""
    try:
        refresh_token = RefreshToken.objects.get(
            token=token,
            is_revoked=False,
            expires_at__gt=datetime.utcnow()
        )
        return refresh_token
    except RefreshToken.DoesNotExist:
        return None


def revoke_refresh_token(token):
    """Revoke a refresh token"""
    try:
        refresh_token = RefreshToken.objects.get(token=token)
        refresh_token.is_revoked = True
        refresh_token.save()
        return True
    except RefreshToken.DoesNotExist:
        return False


def generate_pkce_challenge(verifier):
    """Generate PKCE code challenge from verifier"""
    import hashlib
    import base64
    
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).decode().rstrip('=')
    return challenge