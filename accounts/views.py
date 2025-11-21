from datetime import timezone
import traceback
from django.contrib.auth import get_user_model
User = get_user_model()
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser ,IsAuthenticated
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer
)
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from orders.models import Order
from cart.models import Cart
from wishlist.models import Wishlist
from django.db.models import Sum, Count
from rest_framework import status
from django.utils.html import strip_tags
from django.contrib.auth import authenticate, login
from rest_framework_simplejwt.tokens import RefreshToken



class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.save()

            # Send Welcome Email
            subject = "Welcome to MyStore!"
            html_content = render_to_string('emails/welcome_email.html', {'user': user})
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]

            try:
                email = EmailMultiAlternatives(subject, '', from_email, to_email)
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)
            except Exception as e:
                print("Email failed:", e)

            return Response({"message": "Registration successful!"}, status=201)

        return Response(serializer.errors, status=400)



# In your views.py - LoginView
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data.get('email')
            password = serializer.validated_data.get('password')
            
            # Try to find user by email
            user = None
            try:
                user = User.objects.get(email=email)
                # Check if password is correct
                if not user.check_password(password):
                    user = None
            except User.DoesNotExist:
                pass

            if user is not None:
                if user.is_active:
                    # Generate tokens
                    refresh = RefreshToken.for_user(user)
                    
                    # User data - match frontend expectations
                    user_data = {
                        'id': user.id,
                        'email': user.email,
                        'username': user.username,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_staff': user.is_staff,
                        'is_admin': user.is_staff,  # Frontend checks this
                        'is_active': user.is_active,
                    }
                    
                    # ✅ Return flat structure to match frontend expectations
                    return Response({
                        "message": "Login successful",
                        "access": str(refresh.access_token),
                        "refresh": str(refresh),
                        "user": user_data
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        "error": "Account is disabled."
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    "error": "Invalid email or password."
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Return serializer errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({
            "id": request.user.id,
            "email": request.user.email,
            "username": request.user.username
        })


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        user = request.user
        old = request.data.get("old_password")
        new = request.data.get("new_password")

        if not user.check_password(old):
            return Response({"error": "Old password incorrect"}, status=400)

        user.set_password(new)
        user.save()
        return Response({"message": "Password changed successfully"})


class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            users = User.objects.all().order_by('-date_joined')
            
            user_data = []
            for user in users:
                # Get user statistics
                orders = Order.objects.filter(user=user)
                cart_items = Cart.objects.filter(user=user).count()
                wishlist_items = Wishlist.objects.filter(user=user).count()
                total_spent = orders.aggregate(total_spent=Sum('total'))['total_spent'] or 0
                
                user_data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'full_name': f"{user.first_name} {user.last_name}".strip() if user.first_name or user.last_name else user.username,
                    'phone': getattr(user, 'phone', ''),
                    'is_active': user.is_active,
                    'is_blocked': getattr(user, 'isBlocked', False),
                    'date_joined': user.date_joined,
                    'last_login': user.last_login,
                    'order_count': orders.count(),
                    'total_spent': float(total_spent),
                    'cart_items': cart_items,
                    'wishlist_items': wishlist_items,
                })
            
            return Response({
                'success': True,
                'data': user_data,
                'total': users.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class AdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            
            # Get orders count and statistics
            orders = Order.objects.filter(user=user)
            total_orders = orders.count()
            
            # Calculate order status counts safely
            completed_orders = orders.filter(status__in=['delivered', 'completed', 'Delivered', 'Completed']).count()
            cancelled_orders = orders.filter(status__in=['cancelled', 'Cancelled']).count()
            
            # Calculate total spent
            total_spent_result = orders.aggregate(total_spent=Sum('total'))
            total_spent = float(total_spent_result['total_spent'] or 0)
            
            # Get cart and wishlist counts
            cart_count = Cart.objects.filter(user=user).count()
            wishlist_count = Wishlist.objects.filter(user=user).count()
            
            # Get recent orders (last 10)
            recent_orders = orders.order_by('-date')[:10] if hasattr(Order, 'date') else orders.order_by('-created_at')[:10]
            order_data = []
            for order in recent_orders:
                order_data.append({
                    'id': order.id,
                    'date': getattr(order, 'date', getattr(order, 'created_at', timezone.now())).strftime('%Y-%m-%d'),
                    'total': float(getattr(order, 'total', 0)),
                    'status': getattr(order, 'status', 'unknown'),
                    'payment_method': getattr(order, 'payment_method', 'N/A'),
                })
            
            # Get cart items
            cart_data = []
            cart_items = Cart.objects.filter(user=user)[:10]  # Limit to 10 items
            for item in cart_items:
                cart_data.append({
                    'id': item.id,
                    'product_name': getattr(item.product, 'name', 'Unknown Product') if item.product else 'Unknown Product',
                    'quantity': getattr(item, 'quantity', 1),
                    'price': float(getattr(item.product, 'price', 0)) if item.product else 0.0,
                })
            
            # Get wishlist items
            wishlist_data = []
            wishlist_items = Wishlist.objects.filter(user=user)[:10]  # Limit to 10 items
            for item in wishlist_items:
                wishlist_data.append({
                    'id': item.id,
                    'product_name': getattr(item.product, 'name', 'Unknown Product') if item.product else 'Unknown Product',
                    'price': float(getattr(item.product, 'price', 0)) if item.product else 0.0,
                    'added_date': getattr(item, 'created_at', timezone.now()).strftime('%Y-%m-%d'),
                })
            
            return Response({
                'success': True,
                'data': {
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'full_name': f"{user.first_name} {user.last_name}".strip() if user.first_name or user.last_name else user.username,
                        'phone': getattr(user, 'phone', 'Not provided'),
                        'is_active': user.is_active,
                        'is_blocked': getattr(user, 'isBlocked', False),
                        'date_joined': user.date_joined.strftime('%Y-%m-%d %H:%M'),
                        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never logged in',
                    },
                    'statistics': {
                        'total_orders': total_orders,
                        'completed_orders': completed_orders,
                        'cancelled_orders': cancelled_orders,
                        'pending_orders': total_orders - completed_orders - cancelled_orders,
                        'total_spent': total_spent,
                        'cart_items': cart_count,
                        'wishlist_items': wishlist_count,
                    },
                    'orders': order_data,
                    'cart': cart_data,
                    'wishlist': wishlist_data,
                }
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"User detail error: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to load user details: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class AdminUserBlockView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            action = request.data.get('action', 'block')
            send_email = request.data.get('send_email', True)
            
            if action == 'block':
                user.is_active = False
                user.isBlocked = True
                message = f"User {user.email} has been blocked successfully"
                
                # Send warning email if requested
                if send_email:
                    self.send_block_warning_email(user, request)
                    
            elif action == 'unblock':
                user.is_active = True
                user.isBlocked = False
                message = f"User {user.email} has been unblocked successfully"
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid action. Use "block" or "unblock"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.save()
            
            return Response({
                'success': True,
                'message': message,
                'data': {
                    'id': user.id,
                    'email': user.email,
                    'is_active': user.is_active,
                    'is_blocked': user.isBlocked,
                }
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def send_block_warning_email(self, user, request):
        """Send warning email to blocked user"""
        try:
            subject = "Account Blocked - Action Required"
            
            context = {
                'user': user,
                'admin_name': request.user.get_full_name() or request.user.username,
                'site_name': getattr(settings, 'SITE_NAME', 'MyStore'),
                'contact_email': getattr(settings, 'CONTACT_EMAIL', 'support@example.com'),
            }
            
            html_message = render_to_string('emails/account_blocked_warning.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            
            print(f"Block warning email sent to {user.email}")
            
        except Exception as e:
            print(f"Failed to send block warning email to {user.email}: {str(e)}")
            # Don't fail the entire request if email fails
            pass

# Add this temporary debug view to your urls.py
class DebugUserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, user_id):
        try:
            print(f"Debug: Fetching user {user_id}")
            user = User.objects.get(id=user_id)
            print(f"Debug: User found: {user.email}")
            
            # Check if related models exist
            print(f"Debug: Order model: {Order}")
            print(f"Debug: Cart model: {Cart}")
            print(f"Debug: Wishlist model: {Wishlist}")
            
            return Response({
                'success': True,
                'debug': {
                    'user_id': user_id,
                    'user_exists': True,
                    'user_email': user.email,
                    'models_exist': {
                        'Order': Order is not None,
                        'Cart': Cart is not None,
                        'Wishlist': Wishlist is not None,
                    }
                }
            })
            
        except User.DoesNotExist:
            print(f"Debug: User {user_id} not found")
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=404)
        except Exception as e:
            print(f"Debug: Error: {str(e)}")
            return Response({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=400)
        

class AdminSendWarningEmailView(APIView):
    """API to manually send warning email to user"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            
            # Send warning email
            subject = "Account Warning - Action Required"
            
            context = {
                'user': user,
                'admin_name': request.user.get_full_name() or request.user.username,
                'site_name': getattr(settings, 'SITE_NAME', 'MyStore'),
                'contact_email': getattr(settings, 'CONTACT_EMAIL', 'support@example.com'),
                'is_manual': True,
                'custom_message': request.data.get('custom_message', ''),
            }
            
            html_message = render_to_string('emails/account_warning.html', context)
            plain_message = strip_tags(html_message)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            
            return Response({
                'success': True,
                'message': f'Warning email sent successfully to {user.email}'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error sending warning email: {str(e)}")
            return Response({
                'success': False,
                'error': f'Failed to send email: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)        