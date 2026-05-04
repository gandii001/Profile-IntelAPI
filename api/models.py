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


class User(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('analyst', 'Analyst'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    github_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    avatar_url = models.URLField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='analyst')
    is_active = models.BooleanField(default=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['github_id']),
            models.Index(fields=['username']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.role})"


class RefreshToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.CharField(max_length=500, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_revoked = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_revoked']),
        ]
    
    def __str__(self):
        return f"RefreshToken for {self.user.username}"


class RequestLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid7, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    method = models.CharField(max_length=10)
    endpoint = models.CharField(max_length=500)
    status_code = models.IntegerField()
    response_time = models.FloatField()  # in milliseconds
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['status_code']),
        ]
    
    def __str__(self):
        return f"{self.method} {self.endpoint} - {self.status_code}"