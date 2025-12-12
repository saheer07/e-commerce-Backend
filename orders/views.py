from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions  
from django.utils import timezone
from datetime import timedelta
from .models import Order, OrderItem
from products.models import Product
from .serializers import OrderSerializer
from django.db import transaction
import razorpay
from django.conf import settings
import hmac
import hashlib
from rest_framework.permissions import IsAdminUser

# Initialize Razorpay client
razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

class OrderListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by('-purchased_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request):
        user = request.user
        data = request.data

        product_id = data.get("product")
        quantity = int(data.get("quantity", 1))
        payment_method = data.get("payment_method", "COD")
        delivery_charge = float(data.get("delivery_charge", 0))
        total = float(data.get("total", 0))

        try:
            product = Product.objects.select_for_update().get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        if product.stock < quantity:
            return Response({"error": "Not enough stock"}, status=status.HTTP_400_BAD_REQUEST)

        # Reduce stock
        product.stock -= quantity
        product.save(update_fields=['stock'])

        order = Order.objects.create(
            user=user,
            total=total,
            delivery_charge=delivery_charge,
            payment_method=payment_method,
            address=data.get("address", ""),
            customer_name=data.get("customer_name", ""),
            customer_phone=data.get("customer_phone", ""),
            customer_email=data.get("customer_email", ""),
            card_details=data.get("card_details", {}),
        )

        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            price=product.price
        )

        # If Razorpay payment, create order
        if payment_method == 'RAZORPAY':
            razorpay_order = razorpay_client.order.create({
                "amount": int(total * 100),  # in paise
                "currency": "INR",
                "receipt": f"order_{order.id}",
                "payment_capture": 1,
            })
            order.razorpay_order_id = razorpay_order['id']
            order.save()
            return Response({"order": OrderSerializer(order).data, "razorpay_order": razorpay_order})

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CancelOrderAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if order.status == "Cancelled":
            return Response(
                {"error": "This order has already been cancelled"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order.status != "Ordered":
            return Response(
                {"error": f"Cannot cancel order with status '{order.status}'"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        days_since_order = (timezone.now().date() - order.purchased_at.date()).days
        
        if days_since_order > 2:
            return Response(
                {
                    "error": "Cancellation period expired. Orders can only be cancelled within 2 days of purchase.",
                    "days_since_order": days_since_order,
                    "cancellation_deadline": "2 days"
                }, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        reason = request.data.get("reason", "").strip()
        if not reason:
            return Response(
                {"error": "Cancellation reason is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(reason) < 10:
            return Response(
                {"error": "Please provide a detailed reason (at least 10 characters)"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cancel the order
        order.status = "Cancelled"
        order.cancellation_reason = reason
        order.cancelled_at = timezone.now()
        order.save()
        
        # Restock products
        try:
            order_items = OrderItem.objects.filter(order=order)
            if order_items.exists():
                for item in order_items:
                    item.product.stock += item.quantity
                    item.product.save(update_fields=['stock'])
            elif hasattr(order, 'product') and order.product:
                order.product.stock += order.quantity
                order.product.save(update_fields=['stock'])
        except Exception as e:
            print(f"Error restocking products: {e}")
        
        return Response(
            {
                "message": "Order cancelled successfully and stock has been restored",
                "order_id": order.id,
                "status": order.status,
                "cancelled_reason": order.cancellation_reason
            },
            status=status.HTTP_200_OK
        )


class VerifyPaymentAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            razorpay_order_id = request.data.get('razorpay_order_id')
            razorpay_payment_id = request.data.get('razorpay_payment_id')
            razorpay_signature = request.data.get('razorpay_signature')
            
            if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
                return Response(
                    {"error": "Missing payment verification data"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                order = Order.objects.get(
                    razorpay_order_id=razorpay_order_id,
                    user=request.user
                )
            except Order.DoesNotExist:
                return Response(
                    {"error": "Order not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Verify signature
            generated_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode(),
                f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
                hashlib.sha256
            ).hexdigest()
            
            if generated_signature == razorpay_signature:
                order.razorpay_payment_id = razorpay_payment_id
                order.razorpay_signature = razorpay_signature
                order.payment_status = 'COMPLETED'
                order.status = 'Ordered'
                order.save()
                
                return Response(
                    {
                        "message": "Payment verified successfully",
                        "order_id": order.id,
                        "payment_id": razorpay_payment_id
                    },
                    status=status.HTTP_200_OK
                )
            else:
                order.payment_status = 'FAILED'
                order.save()
                
                return Response(
                    {"error": "Payment verification failed"},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            print(f"Payment verification error: {e}")
            return Response(
                {"error": "Payment verification failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminOrderListView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        try:
            orders = Order.objects.all().select_related('user').prefetch_related('items__product').order_by('-purchased_at')
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error fetching admin orders: {e}")
            return Response(
                {"error": "Failed to fetch orders", "detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminOrderDetailView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request, order_id):
        try:
            order = Order.objects.select_related('user').prefetch_related('items__product').get(id=order_id)
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error fetching order detail: {e}")
            return Response(
                {"error": "Failed to fetch order", "detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def put(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            serializer = OrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error updating order: {e}")
            return Response(
                {"error": "Failed to update order", "detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, order_id):
        return self.put(request, order_id)
    
    def delete(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            
            # Restock items before deleting
            try:
                order_items = OrderItem.objects.filter(order=order)
                for item in order_items:
                    item.product.stock += item.quantity
                    item.product.save(update_fields=['stock'])
            except Exception as e:
                print(f"Error restocking during deletion: {e}")
            
            order.delete()
            return Response(
                {"message": "Order deleted successfully"}, 
                status=status.HTTP_200_OK
            )
        except Order.DoesNotExist:
            return Response({"error": "Order not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error deleting order: {e}")
            return Response(
                {"error": "Failed to delete order", "detail": str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )