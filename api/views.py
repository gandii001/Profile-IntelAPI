from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import sync_to_async
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django_ratelimit.decorators import ratelimit
import asyncio
import csv
from django.db.models import Q
from urllib.parse import urlencode

from .models import Profile
from .serializers import ProfileSerializer
from .service import ProfileService
from .query_parser import NaturalLanguageQueryParser
from .decorators import admin_required, authenticated_required


def get_rate_limit_key(group, request):
    """Get rate limit key based on user"""
    if hasattr(request, 'user'):
        return f"{request.user.id}"
    return request.META.get('REMOTE_ADDR', '')


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(ratelimit(key=get_rate_limit_key, rate='60/m', method='ALL'), name='dispatch')
class ProfileListCreateView(APIView):
    """Create or list profiles with advanced filtering, sorting, and pagination"""
    
    @admin_required
    def post(self, request):
        """Create new profile - Admin only"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"POST /api/profiles request received from user: {request.user.username}")
        
        name = request.data.get('name')
        
        if not name or not isinstance(name, str):
            logger.warning(f"Invalid name: {name}")
            return Response(
                {"status": "error", "message": "Missing or empty name"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"Calling ProfileService.fetch_profile_data with name={name}")
        
        # Run async function synchronously
        from asgiref.sync import async_to_sync
        result, error = async_to_sync(ProfileService.fetch_profile_data)(name)
        
        logger.info(f"Service returned: result={result}, error={error}")

        # Handle errors
        if error == "invalid response":
            return Response({
                "status": "error", 
                "message": f"{result} returned an invalid response"
            }, status=status.HTTP_502_BAD_GATEWAY)
        
        if error == "Connection failure":
            return Response(
                {"status": "error", "message": "Connection failure to upstream services"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Serialize database object
        serializer = ProfileSerializer(result)
        
        if error == "Profile already exists":
            response_data = {
                "status": "success", 
                "message": "Profile already exists",
                "data": serializer.data
            }
            return Response(response_data, status=status.HTTP_200_OK)

        response_data = {"status": "success", "data": serializer.data}
        return Response(response_data, status=status.HTTP_201_CREATED)

    @authenticated_required
    def get(self, request):
        """List profiles with advanced filtering, sorting, and pagination"""
        
        try:
            # ===== FILTERING =====
            queryset = Profile.objects.all()
            
            # Exact match filters
            gender = request.query_params.get('gender')
            country_id = request.query_params.get('country_id')
            age_group = request.query_params.get('age_group')
            
            if gender:
                if gender.lower() not in ['male', 'female']:
                    return Response(
                        {"status": "error", "message": "Invalid gender value"},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY
                    )
                queryset = queryset.filter(gender__iexact=gender)
            
            if country_id:
                queryset = queryset.filter(country_id__iexact=country_id)
            
            if age_group:
                valid_groups = ['child', 'teenager', 'adult', 'senior']
                if age_group.lower() not in valid_groups:
                    return Response(
                        {"status": "error", "message": "Invalid age_group value"},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY
                    )
                queryset = queryset.filter(age_group__iexact=age_group)
            
            # Range filters
            min_age = request.query_params.get('min_age')
            max_age = request.query_params.get('max_age')
            min_gender_probability = request.query_params.get('min_gender_probability')
            min_country_probability = request.query_params.get('min_country_probability')
            
            try:
                if min_age:
                    queryset = queryset.filter(age__gte=int(min_age))
                if max_age:
                    queryset = queryset.filter(age__lte=int(max_age))
                if min_gender_probability:
                    queryset = queryset.filter(gender_probability__gte=float(min_gender_probability))
                if min_country_probability:
                    queryset = queryset.filter(country_probability__gte=float(min_country_probability))
            except (ValueError, TypeError):
                return Response(
                    {"status": "error", "message": "Invalid query parameters"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ===== SORTING =====
            sort_by = request.query_params.get('sort_by', 'created_at')
            order = request.query_params.get('order', 'desc')
            
            valid_sort_fields = ['age', 'created_at', 'gender_probability', 'country_probability']
            if sort_by not in valid_sort_fields:
                return Response(
                    {"status": "error", "message": "Invalid sort_by parameter"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if order not in ['asc', 'desc']:
                return Response(
                    {"status": "error", "message": "Invalid order parameter"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            order_prefix = '' if order == 'asc' else '-'
            queryset = queryset.order_by(f'{order_prefix}{sort_by}')
            
            # ===== PAGINATION =====
            try:
                page = int(request.query_params.get('page', 1))
                limit = int(request.query_params.get('limit', 10))
                
                if page < 1:
                    page = 1
                if limit < 1 or limit > 50:
                    limit = 10
            except (ValueError, TypeError):
                return Response(
                    {"status": "error", "message": "Invalid pagination parameters"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate pagination
            total = queryset.count()
            total_pages = (total + limit - 1) // limit  # Ceiling division
            
            start_index = (page - 1) * limit
            end_index = start_index + limit
            
            profiles = queryset[start_index:end_index]
            serializer = ProfileSerializer(profiles, many=True)
            
            # Build pagination links
            base_url = "/api/profiles"
            current_params = request.query_params.copy()
            
            # Self link
            current_params['page'] = page
            current_params['limit'] = limit
            self_link = f"{base_url}?{urlencode(current_params)}"
            
            # Next link
            next_link = None
            if page < total_pages:
                current_params['page'] = page + 1
                next_link = f"{base_url}?{urlencode(current_params)}"
            
            # Previous link
            prev_link = None
            if page > 1:
                current_params['page'] = page - 1
                prev_link = f"{base_url}?{urlencode(current_params)}"
            
            return Response({
                "status": "success",
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "links": {
                    "self": self_link,
                    "next": next_link,
                    "prev": prev_link
                },
                "data": serializer.data
            })
            
        except Exception as e:
            import logging
            logging.error(f"Error in ProfileListCreateView: {str(e)}")
            return Response(
                {"status": "error", "message": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(ratelimit(key=get_rate_limit_key, rate='60/m', method='ALL'), name='dispatch')
class ProfileDetailView(APIView):
    """Retrieve or delete a single profile"""
    
    @authenticated_required
    def get(self, request, profile_id):
        """Get profile by ID"""
        try:
            profile = Profile.objects.get(id=profile_id)
            serializer = ProfileSerializer(profile)
            return Response({
                "status": "success",
                "data": serializer.data
            })
        except Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @admin_required
    def delete(self, request, profile_id):
        """Delete profile - Admin only"""
        try:
            profile = Profile.objects.get(id=profile_id)
            profile.delete()
            return Response({
                "status": "success",
                "message": "Profile deleted successfully"
            })
        except Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(ratelimit(key=get_rate_limit_key, rate='60/m', method='ALL'), name='dispatch')
class ProfileSearchView(APIView):
    """Natural language search endpoint"""
    
    @authenticated_required
    def get(self, request):
        """Search profiles using natural language query"""
        
        query_string = request.query_params.get('q', '').strip()
        
        if not query_string:
            return Response(
                {"status": "error", "message": "Missing or empty parameter"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse natural language query
        parser = NaturalLanguageQueryParser()
        filters = parser.parse(query_string)
        
        if not filters:
            return Response(
                {"status": "error", "message": "Unable to interpret query"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build queryset
        queryset = Profile.objects.all()
        
        if 'gender' in filters:
            queryset = queryset.filter(gender__iexact=filters['gender'])
        
        if 'age_group' in filters:
            queryset = queryset.filter(age_group__iexact=filters['age_group'])
        
        if 'country_id' in filters:
            queryset = queryset.filter(country_id__iexact=filters['country_id'])
        
        if 'min_age' in filters:
            queryset = queryset.filter(age__gte=filters['min_age'])
        
        if 'max_age' in filters:
            queryset = queryset.filter(age__lte=filters['max_age'])
        
        # Pagination
        try:
            page = int(request.query_params.get('page', 1))
            limit = int(request.query_params.get('limit', 10))
            
            if page < 1:
                page = 1
            if limit < 1 or limit > 50:
                limit = 10
        except (ValueError, TypeError):
            page = 1
            limit = 10
        
        # Calculate pagination
        total = queryset.count()
        total_pages = (total + limit - 1) // limit
        
        start_index = (page - 1) * limit
        end_index = start_index + limit
        
        profiles = queryset[start_index:end_index]
        serializer = ProfileSerializer(profiles, many=True)
        
        # Build links
        base_url = "/api/profiles/search"
        current_params = {'q': query_string, 'page': page, 'limit': limit}
        self_link = f"{base_url}?{urlencode(current_params)}"
        
        next_link = None
        if page < total_pages:
            current_params['page'] = page + 1
            next_link = f"{base_url}?{urlencode(current_params)}"
        
        prev_link = None
        if page > 1:
            current_params['page'] = page - 1
            prev_link = f"{base_url}?{urlencode(current_params)}"
        
        return Response({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "links": {
                "self": self_link,
                "next": next_link,
                "prev": prev_link
            },
            "data": serializer.data
        })


@csrf_exempt
@ratelimit(key=get_rate_limit_key, rate='60/m', method='GET')
@authenticated_required
@require_http_methods(["GET"])
def export_profiles(request):
    """Export profiles as CSV"""
    
    # Apply same filters as list view
    queryset = Profile.objects.all()
    
    # Filtering
    gender = request.GET.get('gender')
    country_id = request.GET.get('country_id')
    age_group = request.GET.get('age_group')
    min_age = request.GET.get('min_age')
    max_age = request.GET.get('max_age')
    min_gender_probability = request.GET.get('min_gender_probability')
    min_country_probability = request.GET.get('min_country_probability')
    
    if gender:
        queryset = queryset.filter(gender__iexact=gender)
    if country_id:
        queryset = queryset.filter(country_id__iexact=country_id)
    if age_group:
        queryset = queryset.filter(age_group__iexact=age_group)
    
    try:
        if min_age:
            queryset = queryset.filter(age__gte=int(min_age))
        if max_age:
            queryset = queryset.filter(age__lte=int(max_age))
        if min_gender_probability:
            queryset = queryset.filter(gender_probability__gte=float(min_gender_probability))
        if min_country_probability:
            queryset = queryset.filter(country_probability__gte=float(min_country_probability))
    except (ValueError, TypeError):
        return JsonResponse(
            {"status": "error", "message": "Invalid query parameters"},
            status=400
        )
    
    # Sorting
    sort_by = request.GET.get('sort_by', 'created_at')
    order = request.GET.get('order', 'desc')
    
    valid_sort_fields = ['age', 'created_at', 'gender_probability', 'country_probability']
    if sort_by in valid_sort_fields:
        order_prefix = '' if order == 'asc' else '-'
        queryset = queryset.order_by(f'{order_prefix}{sort_by}')
    
    # Create CSV response
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"profiles_{timestamp}.csv"
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write header
    writer.writerow([
        'id', 'name', 'gender', 'gender_probability', 
        'age', 'age_group', 'country_id', 'country_name', 
        'country_probability', 'created_at'
    ])
    
    # Write data
    for profile in queryset:
        writer.writerow([
            str(profile.id),
            profile.name,
            profile.gender,
            profile.gender_probability,
            profile.age,
            profile.age_group,
            profile.country_id,
            profile.country_name,
            profile.country_probability,
            profile.created_at.isoformat()
        ])
    
    return response