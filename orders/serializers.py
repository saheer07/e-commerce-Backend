from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'price', 'get_total']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'items', 'total', 'delivery_charge', 'payment_method',
            'card_details', 'razorpay_order_id', 'status', 'address',
            'customer_name', 'customer_phone', 'customer_email',
            'purchased_at', 'cancelled_at', 'cancellation_reason'
        ]
        read_only_fields = ['id', 'user', 'status', 'purchased_at', 'cancelled_at']
