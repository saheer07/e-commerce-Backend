# products/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser
from django.utils import timezone
from .models import Product
from .serializers import ProductSerializer

class ProductListCreateAPIView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get(self, request):
        """Get all active (non-deleted) products"""
        products = Product.objects.filter(is_deleted=False).order_by('-created_at')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

    def post(self, request):
        """Create a new product (admin only)"""
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailAPIView(APIView):
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        return [IsAdminUser()]

    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk, is_deleted=False)
        except Product.DoesNotExist:
            return None

    def get(self, request, pk):
        """Get single product details"""
        product = self.get_object(pk)
        if not product:
            return Response(
                {"detail": "Product not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = ProductSerializer(product)
        return Response(serializer.data)

    def put(self, request, pk):
        """Update product (admin only)"""
        product = self.get_object(pk)
        if not product:
            return Response(
                {"detail": "Product not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Partially update product (admin only)"""
        product = self.get_object(pk)
        if not product:
            return Response(
                {"detail": "Product not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Soft delete - move to trash (admin only)"""
        try:
            product = Product.objects.get(pk=pk)
            product.soft_delete()
            return Response(
                {"message": "Product moved to trash successfully"}, 
                status=status.HTTP_200_OK
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )


class ProductTrashListAPIView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """Get all trashed products (admin only)"""
        products = Product.objects.filter(is_deleted=True).order_by('-deleted_at')
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class ProductRestoreAPIView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        """Restore product from trash (admin only)"""
        try:
            product = Product.objects.get(pk=pk, is_deleted=True)
            product.restore()
            serializer = ProductSerializer(product)
            return Response({
                "message": "Product restored successfully",
                "product": serializer.data
            }, status=status.HTTP_200_OK)
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found in trash"}, 
                status=status.HTTP_404_NOT_FOUND
            )


class ProductPermanentDeleteAPIView(APIView):
    permission_classes = [IsAdminUser]

    def delete(self, request, pk):
        """Permanently delete product from database (admin only)"""
        try:
            product = Product.objects.get(pk=pk, is_deleted=True)
            product_name = product.name
            product.delete()  # Permanent deletion
            return Response(
                {"message": f"Product '{product_name}' permanently deleted"}, 
                status=status.HTTP_200_OK
            )
        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found in trash"}, 
                status=status.HTTP_404_NOT_FOUND
            )