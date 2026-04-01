"""Notification URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from notifications.views import NotificationViewSet, NotificationPreferenceViewSet

app_name = 'notifications'

router = DefaultRouter()
router.register(r'', NotificationViewSet, basename='notification')
router.register(r'preferences', NotificationPreferenceViewSet, basename='notification-preference')

urlpatterns = [
    path('', include(router.urls)),
]
