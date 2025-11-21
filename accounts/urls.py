from django.urls import path
from .views import (
    RegisterView, 
    LoginView, 
    ProfileView, 
    ChangePasswordView,
    AdminUserListView,
    AdminUserDetailView,
    AdminUserBlockView,
    DebugUserDetailView
)
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    
    # Admin endpoints
    path('admin/users/', views.AdminUserListView.as_view(), name='admin-users-list'),
    path('admin/users/<int:user_id>/', views.AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:user_id>/block/', views.AdminUserBlockView.as_view(), name='admin-user-block'),
    path('admin/users/<int:user_id>/send-warning/', views.AdminSendWarningEmailView.as_view(), name='admin-send-warning'),
    path('admin/users/<int:user_id>/debug/', views.DebugUserDetailView.as_view(), name='admin-user-debug'),
]