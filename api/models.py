from django.db import models
import uuid
from uuid6  import uuid7


# Create your models here.

#def generate_uuid_v7():
 #   return uuid6.uuid7()

class Profile(models.Model):
    # following the UUID v7 format
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    name = models.CharField(max_length=255, unique=True) # name must be unique for idempotency logic
    #Genderize fields
    gender = models.CharField(max_length=20, null=True)
    gender_probability = models.FloatField()
    #sample_size = models.IntegerField()
    # Agify fields
    age = models.IntegerField()
    age_group = models.CharField(max_length=20)
    # Nationalize fields
    country_id = models.CharField(max_length=10, null=True)
    country_name = models.CharField(max_length=100, null=True)
    country_probability = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['gender']),
            models.Index(fields=['age']),
            models.Index(fields=['country_id']),
            models.Index(fields=['age_group']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.gender})"