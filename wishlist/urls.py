from django.urls import path
from .views import ToggleWishlistView, WishlistListView, RemoveWishlistItemView

urlpatterns = [
    path('toggle/', ToggleWishlistView.as_view(), name='toggle-wishlist'),
    path('wishlist/', WishlistListView.as_view(), name='wishlist-list'),
    path('remove/<int:wishlist_id>/', RemoveWishlistItemView.as_view(), name='wishlist-remove'),
]
