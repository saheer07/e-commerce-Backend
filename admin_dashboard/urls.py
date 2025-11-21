# admin_dashboard/urls.py

from django.urls import path
from .views import (
    AdminDashboardView,
    AdminReportsView,
    DashboardNotificationsView,
    AnalyticsView,
    DashboardAccessLogView,
    # New user management views
    AdminUserListView,
    AdminUserDetailView,
    AdminUserBlockView,
)

app_name = 'admin_dashboard'

urlpatterns = [
    # Dashboard
    path('', AdminDashboardView.as_view(), name='dashboard'),
    path('reports/', AdminReportsView.as_view(), name='reports'),
    path('notifications/', DashboardNotificationsView.as_view(), name='notifications'),
    path('notifications/<int:pk>/', DashboardNotificationsView.as_view(), name='notification-detail'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    path('logs/', DashboardAccessLogView.as_view(), name='access-logs'),
    
    # User Management
    path('users/', AdminUserListView.as_view(), name='user-list'),
    path('users/<int:user_id>/', AdminUserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/block/', AdminUserBlockView.as_view(), name='user-block'),
]