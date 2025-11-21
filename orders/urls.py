from django.urls import path
from .views import OrderListCreateView, CancelOrderAPIView, VerifyPaymentAPIView ,AdminOrderListView , AdminOrderDetailView
    


urlpatterns = [
    path("orders/", OrderListCreateView.as_view(), name="orders"),
    path("orders/<int:order_id>/cancel/", CancelOrderAPIView.as_view(), name="cancel-order"),
    path("orders/verify-payment/", VerifyPaymentAPIView.as_view(), name="verify-payment"),
    path("admin/orders/", AdminOrderListView.as_view(), name="admin-orders"),
    path("admin/orders/<int:order_id>/", AdminOrderDetailView.as_view(), name="admin-order-detail"),
]

