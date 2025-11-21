from rest_framework import serializers
from .models import (
    DashboardLog, DashboardSettings, AdminReport, 
    DashboardNotification, AnalyticsSnapshot
)


class DashboardLogSerializer(serializers.ModelSerializer):
    """Serializer for dashboard access logs"""
    admin_user_name = serializers.CharField(source='admin_user.username', read_only=True)
    
    class Meta:
        model = DashboardLog
        fields = ['id', 'admin_user', 'admin_user_name', 'accessed_at', 'ip_address', 'action']
        read_only_fields = ['id', 'accessed_at']
    
    def to_representation(self, instance):
        """Format datetime for readability"""
        ret = super().to_representation(instance)
        if ret.get('accessed_at'):
            ret['accessed_at'] = instance.accessed_at.strftime('%Y-%m-%d %H:%M:%S')
        return ret


class DashboardSettingsSerializer(serializers.ModelSerializer):
    """Serializer for dashboard configuration settings"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    
    class Meta:
        model = DashboardSettings
        fields = [
            'id', 'created_by', 'created_by_name', 'refresh_interval', 
            'data_retention_days', 'enable_notifications', 'chart_type', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AdminReportSerializer(serializers.ModelSerializer):
    """Serializer for admin-generated reports"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    
    class Meta:
        model = AdminReport
        fields = [
            'id', 'report_type', 'report_type_display', 'created_by', 'created_by_name', 
            'total_records', 'summary_data', 'generated_at'
        ]
        read_only_fields = ['id', 'generated_at']


class DashboardNotificationSerializer(serializers.ModelSerializer):
    """Serializer for dashboard notifications"""
    admin_user_name = serializers.CharField(source='admin_user.username', read_only=True)
    order_id = serializers.IntegerField(source='related_order.id', read_only=True, allow_null=True)
    product_name = serializers.CharField(source='related_product.name', read_only=True, allow_null=True)
    user_name = serializers.CharField(source='related_user.username', read_only=True, allow_null=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = DashboardNotification
        fields = [
            'id', 'admin_user', 'admin_user_name', 'title', 'message', 'priority',
            'priority_display', 'order_id', 'product_name', 'user_name', 
            'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AnalyticsSnapshotSerializer(serializers.ModelSerializer):
    """Serializer for analytics data snapshots"""
    recorded_by_name = serializers.CharField(
        source='recorded_by.username', 
        read_only=True, 
        allow_null=True
    )
    
    class Meta:
        model = AnalyticsSnapshot
        fields = [
            'id', 'snapshot_date', 'total_users', 'active_users', 'new_users_today',
            'total_products', 'available_products', 'out_of_stock_products',
            'total_orders', 'completed_orders', 'pending_orders',
            'total_revenue', 'average_order_value', 'recorded_by', 'recorded_by_name'
        ]
        read_only_fields = ['id', 'snapshot_date']
    
    def to_representation(self, instance):
        """Format datetime and numbers for readability"""
        ret = super().to_representation(instance)
        if ret.get('snapshot_date'):
            ret['snapshot_date'] = instance.snapshot_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Format currency fields
        ret['total_revenue'] = f"${float(ret.get('total_revenue', 0)):.2f}"
        ret['average_order_value'] = f"${float(ret.get('average_order_value', 0)):.2f}"
        
        return ret


# ==================== OPTIONAL: Summary Serializers ====================

class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for dashboard summary stats"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    admin_users = serializers.IntegerField(required=False)
    total_products = serializers.IntegerField()
    available_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField(required=False)
    total_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField(required=False)
    pending_orders = serializers.IntegerField(required=False)
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)


class DashboardResponseSerializer(serializers.Serializer):
    """Complete dashboard response serializer"""
    success = serializers.BooleanField()
    data = serializers.JSONField()
    timestamp = serializers.DateTimeField(required=False)
