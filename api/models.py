from django.db import models
import uuid
import uuid6  


# Create your models here.

def generate_uuid_v7():
    return uuid6.uuid7()

class Profile(models.Model):
    # following the UUID v7 format
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True) # name must be unique for idempotency logic
    #Genderize fields
    gender = models.CharField(max_length=20, null=True)
    gender_probability = models.DecimalField(max_digits=5, decimal_places=2)
    sample_size = models.IntegerField()
    # Agify fields
    age = models.IntegerField()
    age_group = models.CharField(max_length=20)
    # Nationalize fields
    country_id = models.CharField(max_length=10, null=True)
    country_probability = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.gender})"