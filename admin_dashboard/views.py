from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from django.db.models import Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
from .models import (
    DashboardLog, DashboardSettings, AdminReport,
    DashboardNotification, AnalyticsSnapshot
)
from .serializers import (
    DashboardLogSerializer, DashboardSettingsSerializer, AdminReportSerializer,
    DashboardNotificationSerializer, AnalyticsSnapshotSerializer
)

from django.contrib.auth import get_user_model
from products.models import Product
from orders.models import Order
# Import your models - adjust paths as needed
from cart.models import Cart
from wishlist.models import Wishlist
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings



User = get_user_model()
from .email_templates import get_block_email_template, get_unblock_email_template

# Import your models - adjust paths as needed
try:
    from cart.models import Cart
except ImportError:
    Cart = None

try:
    from wishlist.models import Wishlist
except ImportError:
    Wishlist = None
# =====================================================================
#                          ADMIN DASHBOARD VIEW
# =====================================================================



class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            # Log dashboard access
            DashboardLog.objects.create(
                admin_user=request.user,
                ip_address=self.get_client_ip(request),
                action="dashboard_view"
            )

            # Get filter days
            days = self.get_days_param(request)
            cutoff_date = timezone.now() - timedelta(days=days)

            # ====================== USER DATA ======================
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True, isBlocked=False).count()
            blocked_users = User.objects.filter(isBlocked=True).count()
            admin_users = User.objects.filter(role="admin").count()
            new_users_today = User.objects.filter(date_joined__gte=timezone.now().date()).count()

            # ====================== PRODUCT DATA ======================
            total_products = Product.objects.count()
            available_products = Product.objects.filter(
                (Q(quantity__gt=0) | Q(stock__gt=0)),
                is_active=True
            ).count()
            out_of_stock_products = Product.objects.filter(quantity=0, stock=0).count()
            inactive_products = Product.objects.filter(is_active=False).count()

            # ====================== ORDER DATA ======================
            orders = Order.objects.filter(date__gte=cutoff_date).prefetch_related("products")
            total_orders = orders.count()
            completed_orders = orders.filter(status="delivered").count()
            pending_orders = orders.filter(status__in=["pending", "processing"]).count()
            shipped_orders = orders.filter(status__in=["shipped", "confirmed"]).count()
            cancelled_orders = orders.filter(status="cancelled").count()

            total_revenue = orders.aggregate(total=Sum("total"))["total"] or 0
            avg_order_value = orders.aggregate(avg=Avg("total"))["avg"] or 0
            conversion_rate = (total_orders / total_users * 100) if total_users > 0 else 0

            # ================= TOP PRODUCTS & CUSTOMERS =================
            top_products = self.get_top_products(orders)
            top_customers = self.get_top_customers(orders)

            # ====================== NOTIFICATIONS ======================
            unread_notifications = DashboardNotification.objects.filter(
                admin_user=request.user, is_read=False
            )
            recent_notifications = unread_notifications[:5]

            # ====================== RECENT ACTIVITY ======================
            recent_logs = DashboardLog.objects.filter(admin_user=request.user).order_by("-accessed_at")[:10]

            # ====================== RECENT ORDERS ======================
            recent_orders_data = [
                {
                    "id": o.id,
                    "customer": o.user.username,
                    "total": float(o.total),
                    "status": o.status,
                    "date": o.date.isoformat()
                }
                for o in orders.order_by("-date")[:5]
            ]

            # ====================== SAVE SNAPSHOT ======================
            AnalyticsSnapshot.objects.create(
                total_users=total_users,
                active_users=active_users,
                new_users_today=new_users_today,
                total_products=total_products,
                available_products=available_products,
                out_of_stock_products=out_of_stock_products,
                total_orders=total_orders,
                completed_orders=completed_orders,
                pending_orders=pending_orders,
                total_revenue=float(total_revenue),
                average_order_value=float(avg_order_value),
                recorded_by=request.user
            )

            # ====================== FINAL RESPONSE ======================
            return Response({
                "success": True,
                "data": {
                    "summary": {
                        "total_users": total_users,
                        "active_users": active_users,
                        "blocked_users": blocked_users,
                        "admin_users": admin_users,
                        "new_users_today": new_users_today,
                        "total_products": total_products,
                        "available_products": available_products,
                        "out_of_stock_products": out_of_stock_products,
                        "inactive_products": inactive_products,
                        "total_orders": total_orders,
                        "completed_orders": completed_orders,
                        "pending_orders": pending_orders,
                        "shipped_orders": shipped_orders,
                        "cancelled_orders": cancelled_orders,
                        "total_revenue": float(total_revenue),
                        "average_order_value": float(avg_order_value),
                        "conversion_rate": round(conversion_rate, 2),
                    },
                    "top_products": top_products,
                    "top_customers": top_customers,
                    "recent_orders": recent_orders_data,
                    "notifications": {
                        "unread_count": unread_notifications.count(),
                        "recent": DashboardNotificationSerializer(recent_notifications, many=True).data
                    },
                    "recent_activity": DashboardLogSerializer(recent_logs, many=True).data,
                    "period_days": days,
                    "timestamp": timezone.now().isoformat()
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    # -------- Helper Methods -------- #

    def get_days_param(self, request):
        days = request.query_params.get("days", 30)
        try:
            days = int(days)
            return days if days > 0 else 30
        except:
            return 30

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        return x_forwarded_for.split(",")[0] if x_forwarded_for else request.META.get("REMOTE_ADDR")

    def get_top_products(self, orders):
        product_sales = {}
        for order in orders:
            for item in order.products.all():
                pid = item.product.id
                if pid not in product_sales:
                    product_sales[pid] = {
                        "id": pid,
                        "name": item.product.name,
                        "price": float(item.product.price),
                        "quantity_sold": 0,
                        "total_revenue": 0
                    }
                product_sales[pid]["quantity_sold"] += item.quantity
                product_sales[pid]["total_revenue"] += float(item.price * item.quantity)

        return sorted(product_sales.values(), key=lambda x: x["total_revenue"], reverse=True)[:5]

    def get_top_customers(self, orders):
        customer_data = {}
        for order in orders:
            uid = order.user.id
            if uid not in customer_data:
                customer_data[uid] = {
                    "id": uid,
                    "username": order.user.username,
                    "email": order.user.email,
                    "phone": getattr(order.user, "phone", "N/A"),
                    "orders_count": 0,
                    "total_spent": 0.0
                }

            customer_data[uid]["orders_count"] += 1
            customer_data[uid]["total_spent"] += float(order.total)

        for cust in customer_data.values():
            cust["average_order_value"] = round(cust["total_spent"] / cust["orders_count"], 2)

        return sorted(customer_data.values(), key=lambda x: x["total_spent"], reverse=True)[:5]


# =====================================================================
#                         REPORT GENERATOR VIEW
# =====================================================================

class AdminReportsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            report_type = request.query_params.get("type", None)
            reports = AdminReport.objects.all()

            if report_type:
                reports = reports.filter(report_type=report_type)

            serializer = AdminReportSerializer(reports.order_by("-generated_at"), many=True)

            return Response({
                "success": True,
                "data": serializer.data,
                "total": reports.count()
            })
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)

    def post(self, request):
        try:
            report_type = request.data.get("report_type")
            if not report_type:
                return Response({"success": False, "error": "report_type is required"}, status=400)

            valid_types = ["sales", "products", "users", "inventory"]
            if report_type not in valid_types:
                return Response({"success": False, "error": f"Invalid report_type. Must be: {valid_types}"}, status=400)

            report = None

            # SALES REPORT
            if report_type == "sales":
                orders = Order.objects.all()
                report = AdminReport.objects.create(
                    report_type="sales",
                    created_by=request.user,
                    total_records=orders.count(),
                    summary_data={
                        "total_revenue": float(orders.aggregate(Sum("total"))["total__sum"] or 0),
                        "average_order_value": float(orders.aggregate(Avg("total"))["total__avg"] or 0),
                        "total_orders": orders.count(),
                    }
                )
                report.related_orders.set(orders)

            # PRODUCT REPORT
            if report_type == "products":
                products = Product.objects.all()
                available = products.filter(Q(quantity__gt=0) | Q(stock__gt=0), is_active=True).count()
                report = AdminReport.objects.create(
                    report_type="products",
                    created_by=request.user,
                    total_records=products.count(),
                    summary_data={
                        "total_products": products.count(),
                        "available_products": available,
                        "out_of_stock": products.count() - available,
                    }
                )
                report.related_products.set(products)

            # USERS REPORT
            if report_type == "users":
                users = User.objects.all()
                active_users = users.filter(is_active=True, isBlocked=False).count()
                report = AdminReport.objects.create(
                    report_type="users",
                    created_by=request.user,
                    total_records=users.count(),
                    summary_data={
                        "total_users": users.count(),
                        "active_users": active_users,
                        "blocked_users": users.filter(isBlocked=True).count(),
                    }
                )
                report.related_users.set(users)

            # INVENTORY REPORT
            if report_type == "inventory":
                products = Product.objects.all()
                low_stock = products.filter(Q(quantity__lt=5) | Q(stock__lt=5)).count()
                report = AdminReport.objects.create(
                    report_type="inventory",
                    created_by=request.user,
                    total_records=products.count(),
                    summary_data={
                        "total_products": products.count(),
                        "low_stock": low_stock,
                        "out_of_stock": products.filter(quantity=0, stock=0).count(),
                    }
                )
                report.related_products.set(products)

            return Response({
                "success": True,
                "message": f"{report_type.capitalize()} report generated successfully",
                "data": AdminReportSerializer(report).data
            }, status=201)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)


# =====================================================================
#                         NOTIFICATIONS VIEW
# =====================================================================

class DashboardNotificationsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            is_read = request.query_params.get("is_read")

            notifications = DashboardNotification.objects.filter(
                admin_user=request.user
            ).order_by("-created_at")

            if is_read is not None:
                notifications = notifications.filter(is_read=is_read.lower() == "true")

            serializer = DashboardNotificationSerializer(notifications, many=True)

            return Response({
                "success": True,
                "data": serializer.data,
                "unread_count": DashboardNotification.objects.filter(
                    admin_user=request.user, is_read=False
                ).count()
            })
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)

    def post(self, request):
        try:
            notification = DashboardNotification.objects.create(
                admin_user=request.user,
                title=request.data.get("title", "Notification"),
                message=request.data.get("message", ""),
                priority=request.data.get("priority", "medium")
            )

            return Response({
                "success": True,
                "data": DashboardNotificationSerializer(notification).data
            }, status=201)

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)

    def patch(self, request, pk=None):
        try:
            notification = DashboardNotification.objects.get(pk=pk, admin_user=request.user)
            notification.is_read = True
            notification.save()

            return Response({
                "success": True,
                "message": "Notification marked as read",
                "data": DashboardNotificationSerializer(notification).data
            })

        except DashboardNotification.DoesNotExist:
            return Response({"success": False, "error": "Notification not found"}, status=404)
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)


# =====================================================================
#                         ANALYTICS SNAPSHOT VIEW
# =====================================================================

class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            days = request.query_params.get("days", 30)
            try:
                days = int(days)
            except:
                days = 30

            cutoff = timezone.now() - timedelta(days=days)
            snapshots = AnalyticsSnapshot.objects.filter(snapshot_date__gte=cutoff).order_by("-snapshot_date")

            return Response({
                "success": True,
                "data": AnalyticsSnapshotSerializer(snapshots, many=True).data,
                "total": snapshots.count(),
                "period_days": days
            })

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)


# =====================================================================
#                         ACCESS LOG VIEW
# =====================================================================

class DashboardAccessLogView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            days = request.query_params.get("days", 7)
            try:
                days = int(days)
            except:
                days = 7

            cutoff = timezone.now() - timedelta(days=days)

            logs = DashboardLog.objects.filter(
                admin_user=request.user,
                accessed_at__gte=cutoff
            ).order_by("-accessed_at")[:100]

            return Response({
                "success": True,
                "data": DashboardLogSerializer(logs, many=True).data,
                "total": logs.count()
            })

        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=400)


# =====================================================================
#                      USER MANAGEMENT VIEWS
# =====================================================================

class AdminUserListView(APIView):
    """List all users with stats"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        try:
            users = User.objects.all().order_by('-date_joined')
            
            user_data = []
            for user in users:
                # Get user statistics
                orders = Order.objects.filter(user=user)
                cart_items = Cart.objects.filter(user=user).count() if Cart else 0
                wishlist_items = Wishlist.objects.filter(user=user).count() if Wishlist else 0
                
                user_data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'full_name': getattr(user, 'full_name', '') or f"{user.first_name} {user.last_name}".strip() or user.username,
                    'phone': getattr(user, 'phone', ''),
                    'is_active': user.is_active,
                    'is_blocked': user.isBlocked,
                    'role': getattr(user, 'role', 'user'),
                    'date_joined': user.date_joined.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'order_count': orders.count(),
                    'total_spent': float(orders.aggregate(Sum('total'))['total__sum'] or 0),
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
    """Get detailed information about a specific user"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            
            # Get orders with details
            orders = Order.objects.filter(user=user).prefetch_related('products')
            order_data = []
            for order in orders:
                items = order.products.all()
                order_data.append({
                    'id': order.id,
                    'date': order.date.isoformat(),
                    'total': float(order.total),
                    'status': order.status,
                    'payment_method': order.payment_method,
                    'product_name': items[0].product.name if items else 'N/A',
                    'product_image': items[0].product.image.url if items and hasattr(items[0].product, 'image') and items[0].product.image else None,
                    'quantity': items[0].quantity if items else 0,
                })
            
            # Get cart items
            cart_data = []
            if Cart:
                cart_items = Cart.objects.filter(user=user).select_related('product')
                cart_data = [{
                    'id': item.id,
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'product_image': item.product.image.url if hasattr(item.product, 'image') and item.product.image else None,
                    'quantity': item.quantity,
                    'price': float(item.product.price),
                } for item in cart_items]
            
            # Get wishlist items
            wishlist_data = []
            if Wishlist:
                wishlist_items = Wishlist.objects.filter(user=user).select_related('product')
                wishlist_data = [{
                    'id': item.id,
                    'product_id': item.product.id,
                    'product_name': item.product.name,
                    'product_image': item.product.image.url if hasattr(item.product, 'image') and item.product.image else None,
                    'price': float(item.product.price),
                } for item in wishlist_items]
            
            # Calculate statistics
            total_orders = orders.count()
            completed_orders = orders.filter(status='delivered').count()
            cancelled_orders = orders.filter(status='cancelled').count()
            total_spent = float(orders.aggregate(Sum('total'))['total__sum'] or 0)
            
            return Response({
                'success': True,
                'data': {
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'full_name': getattr(user, 'full_name', '') or f"{user.first_name} {user.last_name}".strip() or user.username,
                        'phone': getattr(user, 'phone', ''),
                        'is_active': user.is_active,
                        'is_blocked': user.isBlocked,
                        'blocked_at': user.blocked_at.isoformat() if hasattr(user, 'blocked_at') and user.blocked_at else None,
                        'block_reason': getattr(user, 'block_reason', ''),
                        'role': getattr(user, 'role', 'user'),
                        'date_joined': user.date_joined.isoformat(),
                        'last_login': user.last_login.isoformat() if user.last_login else None,
                    },
                    'statistics': {
                        'total_orders': total_orders,
                        'completed_orders': completed_orders,
                        'cancelled_orders': cancelled_orders,
                        'total_spent': total_spent,
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
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class AdminUserBlockView(APIView):
    """Block or unblock a user with email notification"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            action = request.data.get('action', 'block')
            custom_message = request.data.get('message', '')
            use_default_message = request.data.get('use_default_message', True)
            
            if action == 'block':
                if user.isBlocked:
                    return Response({
                        'success': False,
                        'error': 'User is already blocked'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Block the user
                user.isBlocked = True
                user.is_active = False
                if hasattr(user, 'blocked_at'):
                    user.blocked_at = timezone.now()
                if hasattr(user, 'blocked_by'):
                    user.blocked_by = request.user
                if hasattr(user, 'block_reason'):
                    user.block_reason = custom_message if not use_default_message else "Your account has been blocked by the administrator."
                user.save()
                
                # Send email notification
                self.send_block_email(user, custom_message, use_default_message)
                
                message = f"User {user.email} has been blocked successfully"
                
            elif action == 'unblock':
                if not user.isBlocked:
                    return Response({
                        'success': False,
                        'error': 'User is not blocked'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Unblock the user
                user.isBlocked = False
                user.is_active = True
                if hasattr(user, 'blocked_at'):
                    user.blocked_at = None
                if hasattr(user, 'blocked_by'):
                    user.blocked_by = None
                if hasattr(user, 'block_reason'):
                    user.block_reason = ''
                user.save()
                
                # Send unblock email
                self.send_unblock_email(user, custom_message, use_default_message)
                
                message = f"User {user.email} has been unblocked successfully"
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid action. Use "block" or "unblock"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create notification log
            DashboardLog.objects.create(
                admin_user=request.user,
                ip_address=self.get_client_ip(request),
                action=f"{action}_user_{user.id}"
            )
            
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
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
    
    def send_block_email(self, user, custom_message, use_default):
        """Send email notification when user is blocked"""
        try:
            subject = "Account Access Suspended"
            
            # Get email template
            if use_default:
                html_message = get_block_email_template(user, None)
            else:
                html_message = get_block_email_template(user, custom_message)
            
            # Create plain text version
            text_content = strip_tags(html_message)
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
        except Exception as e:
            print(f"Failed to send block email: {str(e)}")
    
    def send_unblock_email(self, user, custom_message, use_default):
        """Send email notification when user is unblocked"""
        try:
            subject = "Account Access Restored"
            
            # Get email template
            if use_default:
                html_message = get_unblock_email_template(user, None)
            else:
                html_message = get_unblock_email_template(user, custom_message)
            
            # Create plain text version
            text_content = strip_tags(html_message)
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            
        except Exception as e:
            print(f"Failed to send unblock email: {str(e)}")