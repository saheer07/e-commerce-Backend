# Updated User model (accounts/models.py)

from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    isBlocked = models.BooleanField(default=False)
    phone = models.CharField(max_length=20)
    
    # Additional fields for enhanced admin functionality
    blocked_at = models.DateTimeField(null=True, blank=True)
    blocked_by = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='blocked_users'
    )
    block_reason = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    full_name = models.CharField(max_length=255, blank=True)
    
    # Role field for admin identification
    ROLE_CHOICES = (
        ('user', 'User'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    USERNAME_FIELD = 'email'    
    REQUIRED_FIELDS = ['username'] 

    class Meta:
        ordering = ['-date_joined']

    def __str__(self):
        return self.email