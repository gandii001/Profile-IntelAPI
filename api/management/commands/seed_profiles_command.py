import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
import pycountry
from api.models import Profile


def get_country_name(country_code):
    """Get country name from ISO code using pycountry"""
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        return country.name if country else "Unknown"
    except:
        return "Unknown"


class Command(BaseCommand):
    help = 'Seed the database with profiles from seed_profiles.json'

    def handle(self, *args, **options):
        # Get path to seed file
        seed_file = os.path.join(
            settings.BASE_DIR, 'seed_profiles.json'
        )

        if not os.path.exists(seed_file):
            self.stdout.write(
                self.style.ERROR(f'Seed file not found: {seed_file}')
            )
            return

        # Read seed data
        with open(seed_file, 'r') as f:
            data = json.load(f)

        profiles = data.get('profiles', [])
        created_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(
            self.style.SUCCESS(f'Starting to seed {len(profiles)} profiles...')
        )

        for profile_data in profiles:
            try:
                name = profile_data.get('name', '').lower()
                
                if not name:
                    error_count += 1
                    continue

                # Check if profile already exists (idempotency)
                existing = Profile.objects.filter(name__iexact=name).first()
                
                if existing:
                    skipped_count += 1
                    continue

                # Get country name from code
                country_code = profile_data.get('country_id')
                country_name = get_country_name(country_code)

                # Create profile
                Profile.objects.create(
                    name=name,
                    gender=profile_data.get('gender'),
                    gender_probability=float(profile_data.get('gender_probability', 0)),
                    age=int(profile_data.get('age', 0)),
                    age_group=profile_data.get('age_group'),
                    country_id=country_code,
                    country_name=country_name,
                    country_probability=float(profile_data.get('country_probability', 0))
                )
                created_count += 1

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Error creating profile {profile_data.get("name")}: {str(e)}')
                )
                continue

        # Print summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Seeding Complete!\n'
                f'  Created: {created_count}\n'
                f'  Skipped (already exist): {skipped_count}\n'
                f'  Errors: {error_count}\n'
                f'  Total in DB: {Profile.objects.count()}'
            )
        )