from functools import wraps
from django.http import JsonResponse


def require_role(*allowed_roles):
    """Decorator to require specific roles for a view"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            # Check if user is authenticated (middleware should set this)
            if not hasattr(request, 'user'):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Authentication required'
                }, status=401)
            
            # Check if user has required role
            if request.user_role not in allowed_roles:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Insufficient permissions'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator


def admin_required(view_func):
    """Decorator to require admin role"""
    return require_role('admin')(view_func)


def authenticated_required(view_func):
    """Decorator to require authentication (any role)"""
    return require_role('admin', 'analyst')(view_func)