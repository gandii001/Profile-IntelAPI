from django.shortcuts import render
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.decorators import api_view, APIView
import requests
from datetime import datetime, timezone
import asyncio
import httpx
from django.conf import settings
from .models import Profile
import pycountry


def get_country_name(country_code):
    """Get country name from ISO 2-letter code using pycountry"""
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        return country.name if country else "Unknown"
    except:
        return "Unknown"


class ProfileService:
    @staticmethod
    def classify_age_group(age):
        if age <= 12:
            return "child"
        elif age <= 19:
            return "teenager"
        elif age <= 59:
            return "adult"
        else:
            return "senior"
    
    @staticmethod
    async def fetch_profile_data(name):
        #checks if profile is already in database
        existing = await Profile.objects.filter(name__iexact=name).afirst()
        if existing:
            return existing, "Profile already exists"
        
        async with httpx.AsyncClient(timeout=10) as client:
            try:
                #gathers them and runs them concurrently, and waits for all of them to complete before proceeding
                response = await asyncio.gather(
                client.get(f"https://api.genderize.io?name={name}"),
                client.get(f"https://api.agify.io?name={name}"),
                client.get(f"https://api.nationalize.io?name={name}"))
            except Exception:
                return None, "Connection failure to upstream services"

            # Parse JSON
            gender_data, age_data, nation_data = [res.json() for res in response]

            # Edge Case Validation (Requirement 502)
            if not gender_data.get("gender") or gender_data.get("count") == 0:
                return "Genderize", "invalid response"
            if age_data.get("age") is None:
                return "Agify", "invalid response"
            if not nation_data.get("country"):
                return "Nationalize", "invalid response"

            # Data Transformation
            top_country = max(nation_data["country"], key=lambda x: x["probability"])
            country_id = top_country["country_id"]
            country_name = get_country_name(country_id)
            
            # Persistence
            new_profile = await Profile.objects.acreate(
                name=name.lower(),
                gender=gender_data["gender"],
                gender_probability=gender_data["probability"],
                age=age_data["age"],
                age_group=ProfileService.classify_age_group(age_data["age"]),
                country_id=country_id,
                country_name=country_name,
                country_probability=top_country["probability"]
            )
            return new_profile, None