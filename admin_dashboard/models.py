from django.db import models
from django.contrib.auth import get_user_model
# REMOVE direct imports - use string references instead
# from products.models import Product
# from orders.models import Order

# Correct User model import
User = get_user_model()


class DashboardLog(models.Model):
    """Track admin dashboard access"""
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_logs')
    accessed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    action = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-accessed_at']
        verbose_name = 'Dashboard Log'
        verbose_name_plural = 'Dashboard Logs'

    def __str__(self):
        return f"{self.admin_user} - {self.accessed_at}"


class DashboardSettings(models.Model):
    """Admin Dashboard Settings"""
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_settings')
    refresh_interval = models.IntegerField(default=30)
    data_retention_days = models.IntegerField(default=365)
    enable_notifications = models.BooleanField(default=True)
    chart_type = models.CharField(
        max_length=50,
        default='bar',
        choices=[
            ('bar', 'Bar Chart'),
            ('line', 'Line Chart'),
            ('pie', 'Pie Chart'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Dashboard Settings'
        verbose_name_plural = 'Dashboard Settings'

    def __str__(self):
        return "Dashboard Configuration"


class AdminReport(models.Model):
    """Generate and store admin reports"""
    REPORT_TYPE_CHOICES = (
        ('sales', 'Sales Report'),
        ('users', 'Users Report'),
        ('products', 'Products Report'),
        ('inventory', 'Inventory Report'),
    )

    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_reports')

    # Use string references instead of direct imports
    related_orders = models.ManyToManyField('orders.Order', blank=True, related_name='reports')
    related_products = models.ManyToManyField('products.Product', blank=True, related_name='reports')
    related_users = models.ManyToManyField(User, blank=True, related_name='user_reports')

    total_records = models.IntegerField(default=0)
    summary_data = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']
        verbose_name = 'Admin Report'
        verbose_name_plural = 'Admin Reports'

    def __str__(self):
        return f"{self.get_report_type_display()} - {self.created_by}"


class DashboardNotification(models.Model):
    """Admin notifications for important events"""
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )

    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')

    # Use string references instead of direct imports
    related_order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    related_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_notifications')

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Dashboard Notification'
        verbose_name_plural = 'Dashboard Notifications'

    def __str__(self):
        return f"{self.title} - {self.admin_user}"


class AnalyticsSnapshot(models.Model):
    """Store analytics data snapshots at intervals"""
    snapshot_date = models.DateTimeField(auto_now_add=True)

    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    new_users_today = models.IntegerField(default=0)

    total_products = models.IntegerField(default=0)
    available_products = models.IntegerField(default=0)
    out_of_stock_products = models.IntegerField(default=0)

    total_orders = models.IntegerField(default=0)
    completed_orders = models.IntegerField(default=0)
    pending_orders = models.IntegerField(default=0)

    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='analytics_snapshots')

    class Meta:
        ordering = ['-snapshot_date']
        verbose_name = 'Analytics Snapshot'
        verbose_name_plural = 'Analytics Snapshots'

    def __str__(self):
        return f"Snapshot - {self.snapshot_date.strftime('%Y-%m-%d %H:%M')}"