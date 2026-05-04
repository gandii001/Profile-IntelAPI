from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from .auth_utils import verify_access_token
from .models import User, RequestLog
import time


class AuthenticationMiddleware(MiddlewareMixin):
    """Middleware to authenticate requests using JWT tokens"""
    
    # Paths that don't require authentication
    EXEMPT_PATHS = [
        '/auth/github',
        '/auth/github/callback',
        '/auth/refresh',
        '/admin/',
        '/health',
    ]
    
    def process_request(self, request):
        # Skip authentication for exempt paths
        if any(request.path.startswith(path) for path in self.EXEMPT_PATHS):
            return None
        
        # Skip authentication for non-API paths
        if not request.path.startswith('/api/'):
            return None
        
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header.startswith('Bearer '):
            return JsonResponse({
                'status': 'error',
                'message': 'Authentication required'
            }, status=401)
        
        token = auth_header.replace('Bearer ', '')
        
        # Verify token
        payload = verify_access_token(token)
        
        if not payload:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid or expired token'
            }, status=401)
        
        # Get user
        try:
            user = User.objects.get(id=payload['user_id'])
            
            # Check if user is active
            if not user.is_active:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Account is inactive'
                }, status=403)
            
            # Attach user to request
            request.user = user
            request.user_role = user.role
            
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'User not found'
            }, status=401)
        
        return None


class RequestLoggingMiddleware(MiddlewareMixin):
    """Middleware to log all requests"""
    
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        # Calculate response time
        if hasattr(request, 'start_time'):
            response_time = (time.time() - request.start_time) * 1000  # Convert to ms
            
            # Get user if authenticated
            user = getattr(request, 'user', None)
            if isinstance(user, User):
                user_obj = user
            else:
                user_obj = None
            
            # Get IP address
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            
            # Log the request
            RequestLog.objects.create(
                user=user_obj,
                method=request.method,
                endpoint=request.path,
                status_code=response.status_code,
                response_time=response_time,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
            )
        
        return response


class APIVersionMiddleware(MiddlewareMixin):
    """Middleware to check API version header"""
    
    def process_request(self, request):
        # Only check for /api/ endpoints
        if not request.path.startswith('/api/'):
            return None
        
        # Check for API version header
        api_version = request.META.get('HTTP_X_API_VERSION')
        
        if not api_version:
            return JsonResponse({
                'status': 'error',
                'message': 'API version header required'
            }, status=400)
        
        # Validate version
        if api_version != '1':
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid API version'
            }, status=400)
        
        return None