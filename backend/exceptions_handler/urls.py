"""Exception handling URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from exceptions_handler.views import PlatformExceptionViewSet

app_name = 'exceptions_handler'

router = DefaultRouter()
router.register(r'', PlatformExceptionViewSet, basename='platform-exception')

urlpatterns = [
    path('', include(router.urls)),
]
