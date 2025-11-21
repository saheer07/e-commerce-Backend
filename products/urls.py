from django.urls import path
from .views import (
    ProductListCreateAPIView,
    ProductDetailAPIView,
    ProductTrashListAPIView,
    ProductRestoreAPIView,
    ProductPermanentDeleteAPIView
)

urlpatterns = [
    path('products/', ProductListCreateAPIView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailAPIView.as_view(), name='product-detail'),
    path('products/trash/', ProductTrashListAPIView.as_view(), name='product-trash'),
    path('products/<int:pk>/restore/', ProductRestoreAPIView.as_view(), name='product-restore'),
    path('products/<int:pk>/permanent/', ProductPermanentDeleteAPIView.as_view(), name='product-permanent-delete'),
]
