# products/serializers.py
from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'brand', 'color', 'description', 'price',
            'category', 'image', 'rating', 'stock', 'created_at',
            'updated_at', 'review_count', 'average_rating', 'is_deleted', 'deleted_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'is_deleted', 'deleted_at']

    def get_review_count(self, obj):
        return obj.reviews.count() if hasattr(obj, 'reviews') else 0

    def get_average_rating(self, obj):
        reviews = getattr(obj, 'reviews', None)
        if not reviews:
            return 0
        reviews_qs = reviews.all() if callable(getattr(reviews, 'all', None)) else reviews
        count = reviews_qs.count()
        if count == 0:
            return 0
        return sum([r.rating for r in reviews_qs]) / count
