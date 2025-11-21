from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import DashboardLog, DashboardSettings, AdminReport, DashboardNotification, AnalyticsSnapshot

@admin.register(DashboardLog)
class DashboardLogAdmin(admin.ModelAdmin):
    list_display = ['admin_user', 'accessed_at', 'action', 'ip_address']
    list_filter = ['accessed_at', 'action']
    search_fields = ['admin_user__username', 'ip_address']
    readonly_fields = ['accessed_at']

@admin.register(DashboardSettings)
class DashboardSettingsAdmin(admin.ModelAdmin):
    list_display = ['refresh_interval', 'chart_type', 'enable_notifications', 'updated_at']

@admin.register(AdminReport)
class AdminReportAdmin(admin.ModelAdmin):
    list_display = ['report_type', 'created_by', 'total_records', 'generated_at']
    list_filter = ['report_type', 'generated_at']
    search_fields = ['created_by__username']
    readonly_fields = ['generated_at']

@admin.register(DashboardNotification)
class DashboardNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'admin_user', 'priority', 'is_read', 'created_at']
    list_filter = ['priority', 'is_read', 'created_at']
    search_fields = ['title', 'admin_user__username']

@admin.register(AnalyticsSnapshot)
class AnalyticsSnapshotAdmin(admin.ModelAdmin):
    list_display = ['snapshot_date', 'total_users', 'total_orders', 'total_revenue']
    list_filter = ['snapshot_date']
    readonly_fields = ['snapshot_date']
