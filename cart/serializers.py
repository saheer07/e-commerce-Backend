from rest_framework import serializers
from .models import Cart
from products.serializers import ProductSerializer

class CartSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'product', 'quantity', 'added_at']
