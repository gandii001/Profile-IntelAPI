from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import sync_to_async
from django.utils.decorators import method_decorator
import asyncio
from django.db.models import Q

from .models import Profile
from .serializers import ProfileSerializer
from .service import ProfileService
from .query_parser import NaturalLanguageQueryParser


@method_decorator(csrf_exempt, name='dispatch')
class ProfileListCreateView(APIView):
    """Create or list profiles with advanced filtering, sorting, and pagination"""
    
    def post(self, request):
        """Create new profile - SYNC wrapper for async service"""
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"POST /api/profiles request received")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request content-type: {request.content_type}")
        logger.info(f"Request data: {request.data}")
        
        name = request.data.get('name')
        logger.info(f"Extracted name: {name}")
        
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
            
            if min_age:
                try:
                    min_age = int(min_age)
                    if min_age < 0:
                        return Response(
                            {"status": "error", "message": "min_age must be >= 0"},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY
                        )
                    queryset = queryset.filter(age__gte=min_age)
                except ValueError:
                    return Response(
                        {"status": "error", "message": "min_age must be an integer"},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY
                    )
            
            if max_age:
                try:
                    max_age = int(max_age)
                    if max_age < 0:
                        return Response(
                            {"status": "error", "message": "max_age must be >= 0"},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY
                        )
                    queryset = queryset.filter(age__lte=max_age)
                except ValueError:
                    return Response(
                        {"status": "error", "message": "max_age must be an integer"},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY
                    )
            
            # Probability filters
            min_gender_prob = request.query_params.get('min_gender_probability')
            min_country_prob = request.query_params.get('min_country_probability')
            
            if min_gender_prob:
                try:
                    min_gender_prob = float(min_gender_prob)
                    if not (0 <= min_gender_prob <= 1):
                        return Response(
                            {"status": "error", "message": "Probability must be between 0 and 1"},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY
                        )
                    queryset = queryset.filter(gender_probability__gte=min_gender_prob)
                except ValueError:
                    return Response(
                        {"status": "error", "message": "min_gender_probability must be a float"},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY
                    )
            
            if min_country_prob:
                try:
                    min_country_prob = float(min_country_prob)
                    if not (0 <= min_country_prob <= 1):
                        return Response(
                            {"status": "error", "message": "Probability must be between 0 and 1"},
                            status=status.HTTP_422_UNPROCESSABLE_ENTITY
                        )
                    queryset = queryset.filter(country_probability__gte=min_country_prob)
                except ValueError:
                    return Response(
                        {"status": "error", "message": "min_country_probability must be a float"},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY
                    )
            
            # ===== SORTING =====
            sort_by = request.query_params.get('sort_by', 'created_at')
            order = request.query_params.get('order', 'desc')
            
            valid_sort_fields = ['age', 'created_at', 'gender_probability']
            if sort_by not in valid_sort_fields:
                return Response(
                    {"status": "error", "message": f"Invalid sort_by. Must be one of: {', '.join(valid_sort_fields)}"},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
            
            if order.lower() not in ['asc', 'desc']:
                return Response(
                    {"status": "error", "message": "order must be 'asc' or 'desc'"},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
            
            # Apply sorting
            if order.lower() == 'desc':
                queryset = queryset.order_by(f'-{sort_by}')
            else:
                queryset = queryset.order_by(sort_by)
            
            # ===== PAGINATION =====
            page = request.query_params.get('page', 1)
            limit = request.query_params.get('limit', 10)
            
            try:
                page = int(page)
                limit = int(limit)
                
                if page < 1:
                    return Response(
                        {"status": "error", "message": "page must be >= 1"},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY
                    )
                
                if limit < 1 or limit > 50:
                    return Response(
                        {"status": "error", "message": "limit must be between 1 and 50"},
                        status=status.HTTP_422_UNPROCESSABLE_ENTITY
                    )
            except ValueError:
                return Response(
                    {"status": "error", "message": "page and limit must be integers"},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
            
            # Get total count before slicing
            total_count = queryset.count()
            
            # Apply pagination
            offset = (page - 1) * limit
            paginated_queryset = queryset[offset:offset + limit]
            
            # Serialize
            serializer = ProfileSerializer(paginated_queryset, many=True)
            
            return Response({
                "status": "success",
                "page": page,
                "limit": limit,
                "total": total_count,
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class ProfileSearchView(APIView):
    """Natural language query search for profiles"""
    
    def get(self, request):
        """Search profiles using natural language query"""
        
        q = request.query_params.get('q', '').strip()
        
        if not q:
            return Response(
                {"status": "error", "message": "Missing or empty query parameter 'q'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Parse natural language query
        parser = NaturalLanguageQueryParser(q)
        filters, error = parser.parse()
        parser = NaturalLanguageQueryParser("young males from nigeria")
        print(parser.parse())
        
        if error:
            return Response(
                {"status": "error", "message": error},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        # Build queryset from parsed filters
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
        
        # Handle pagination
        page = request.query_params.get('page', 1)
        limit = request.query_params.get('limit', 10)
        
        try:
            page = int(page)
            limit = int(limit)
            
            if page < 1 or limit < 1 or limit > 50:
                return Response(
                    {"status": "error", "message": "Invalid pagination parameters"},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
        except ValueError:
            return Response(
                {"status": "error", "message": "page and limit must be integers"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        total_count = queryset.count()
        offset = (page - 1) * limit
        paginated_queryset = queryset[offset:offset + limit]
        
        serializer = ProfileSerializer(paginated_queryset, many=True)
        
        return Response({
            "status": "success",
            "page": page,
            "limit": limit,
            "total": total_count,
            "data": serializer.data
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class ProfileDetailView(APIView):
    """Get or delete a specific profile"""
    
    def get(self, request, pk):
        """Get profile by ID"""
        try:
            profile = Profile.objects.get(id=pk)
        except Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProfileSerializer(profile)
        return Response(
            {"status": "success", "data": serializer.data}, 
            status=status.HTTP_200_OK
        )

    def delete(self, request, pk):
        """Delete profile by ID"""
        try:
            profile = Profile.objects.get(id=pk)
        except Profile.DoesNotExist:
            return Response(
                {"status": "error", "message": "Profile not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        profile.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)