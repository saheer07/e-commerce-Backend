from django.urls import path
from . import views

urlpatterns = [
    path('', views.CartListCreateView.as_view(), name='cart'),
    path('add/', views.AddToCartView.as_view(), name='add_to_cart'),
    path('remove/<int:pk>/', views.RemoveFromCartView.as_view(), name='remove_from_cart'),
]
