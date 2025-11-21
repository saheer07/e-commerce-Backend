# products/models.py
from django.db import models

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('Hatchback', 'Hatchback'),
        ('Sedan', 'Sedan'),
        ('SUV', 'SUV'),
        ('Truck', 'Truck'),
    ]

    COLOR_CHOICES = [
        ('Red', 'Red'),
        ('Blue', 'Blue'),
        ('Black', 'Black'),
        ('White', 'White'),
        ('Silver', 'Silver'),
        ('Gray', 'Gray'),
        ('Green', 'Green'),
    ]

    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100, default='Unknown')
    color = models.CharField(max_length=50, choices=COLOR_CHOICES, default='Black')
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Hatchback')
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    stock = models.PositiveIntegerField(default=0)
    
    # Soft delete fields
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    review_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.brand} {self.name}"

    def soft_delete(self):
        """Move product to trash"""
        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restore product from trash"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()