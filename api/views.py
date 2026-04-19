from django.views.decorators.csrf import csrf_exempt
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import sync_to_async
from django.utils.decorators import method_decorator
import asyncio

from .models import Profile
from .serializers import ProfileSerializer
from .service import ProfileService


@method_decorator(csrf_exempt, name='dispatch')
class ProfileListCreateView(APIView):
    """Create or list profiles"""
    
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
        """List profiles with filtering"""
        gender = request.query_params.get('gender')
        country = request.query_params.get('country_id')
        age_group = request.query_params.get('age_group')

        # Build queryset
        queryset = Profile.objects.all()
        
        if gender:
            queryset = queryset.filter(gender__iexact=gender)
        if country:
            queryset = queryset.filter(country_id__iexact=country)
        if age_group:
            queryset = queryset.filter(age_group__iexact=age_group)

        # Convert to list
        profiles = list(queryset)
        
        # For list response, only include specific fields as per spec
        data = []
        for profile in profiles:
            data.append({
                "id": str(profile.id),
                "name": profile.name,
                "gender": profile.gender,
                "age": profile.age,
                "age_group": profile.age_group,
                "country_id": profile.country_id,
            })
        
        return Response({
            "status": "success",
            "count": len(profiles),
            "data": data
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