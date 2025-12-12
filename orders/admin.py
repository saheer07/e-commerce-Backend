# orders/admin.py

from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    fields = ('product', 'quantity', 'price')
    readonly_fields = ('price',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer_name', 'user', 'status', 'payment_method', 
        'total', 'purchased_at'
    )
    list_filter = ['status']
    search_fields = (
        'id', 'customer_name', 'customer_email', 'customer_phone', 
        'tracking_number', 'user__username'
    )
    readonly_fields = ('purchased_at', 'cancelled_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': (
                'user', 'status', 'purchased_at', 'tracking_number', 
                'estimated_delivery'
            )
        }),
        ('Customer Details', {
            'fields': (
                'customer_name', 'customer_email', 'customer_phone', 'address'
            )
        }),
        ('Payment Information', {
            'fields': (
                'payment_method', 'payment_status', 'total', 'delivery_charge',
                'razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature'
            )
        }),
        ('Cancellation', {
            'fields': ('cancelled_at', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Additional Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'purchased_at'
    
    def get_readonly_fields(self, request, obj=None):
        # Make certain fields readonly after creation
        if obj:
            return self.readonly_fields + ('user',)
        return self.readonly_fields

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'product', 'quantity', 'price', 'get_total')
    list_filter = ('order__status',)
    search_fields = ('order__id', 'product__name')
    
    def get_total(self, obj):
        return obj.get_total()
    get_total.short_description = 'Total'