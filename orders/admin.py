from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'status', 'payment_method', 'purchased_at']
    list_filter = ['status', 'payment_method', 'purchased_at']
    search_fields = ['id', 'user__username', 'customer_email']
    inlines = [OrderItemInline]

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity', 'price']
    list_filter = ['order__status']