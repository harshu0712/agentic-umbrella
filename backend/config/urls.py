"""
URL configuration for Agentic Umbrella Platform.
API v1 routing for Module 6 (Compliance) and Module 7 (Audit, Notifications, Exceptions).
"""
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from compliance.views import dashboard_data, users_list
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from core.views import HealthCheckView

urlpatterns = [
    path("api/users/", users_list),
     path('api/token/', TokenObtainPairView.as_view()),   # 🔐 LOGIN
    path('api/token/refresh/', TokenRefreshView.as_view()),  # 🔄 REFRESH
    path("api/dashboard/", dashboard_data),
    # Admin
    path('admin/', admin.site.urls),

    # Health check
    path('api/health/', HealthCheckView.as_view(), name='health-check'),

    # Authentication (JWT)
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token-obtain'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('api/v1/auth/token/verify/', TokenVerifyView.as_view(), name='token-verify'),

    # Module 7 — Audit Log
    path('api/v1/audit/', include('audit.urls', namespace='audit')),

    # Module 7 — Notifications
    path('api/v1/notifications/', include('notifications.urls', namespace='notifications')),

    # Module 7 — Exception Handling
    path('api/v1/exceptions/', include('exceptions_handler.urls', namespace='exceptions_handler')),

    # Module 6 — Compliance Engine
    path('api/v1/compliance/', include('compliance.urls', namespace='compliance')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
