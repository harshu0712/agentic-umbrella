from django.contrib import admin
from notifications.models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'event_type', 'channel', 'status', 'is_read', 'created_at']
    list_filter = ['channel', 'status', 'is_read', 'event_type']
    search_fields = ['recipient__email', 'title', 'message']
    readonly_fields = ['id', 'created_at', 'sent_at']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'event_type', 'email_enabled', 'in_app_enabled']
    list_filter = ['email_enabled', 'event_type']
