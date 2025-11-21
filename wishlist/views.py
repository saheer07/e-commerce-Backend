from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Wishlist
from .serializers import WishlistSerializer
from products.models import Product


# ✅ 1. Add/Remove (Toggle) Wishlist
class ToggleWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get('product_id')

        if not product_id:
            return Response({"error": "Product ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND)

        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)

        if not created:
            wishlist_item.delete()
            return Response(
                {"in_wishlist": False, "message": "Removed from wishlist 💔"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"in_wishlist": True, "message": "Added to wishlist ❤️"},
            status=status.HTTP_201_CREATED
        )


# ✅ 2. Get all wishlist items
class WishlistListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist = Wishlist.objects.filter(user=request.user).select_related('product')
        serializer = WishlistSerializer(wishlist, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ✅ 3. Remove a wishlist item (by wishlist ID)
class RemoveWishlistItemView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, wishlist_id):
        try:
            item = Wishlist.objects.get(id=wishlist_id, user=request.user)
            item.delete()
            return Response({"message": "Item removed from wishlist 💔"}, status=status.HTTP_200_OK)
        except Wishlist.DoesNotExist:
            return Response({"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND)
