from django.contrib import admin
from audit.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """
    Admin interface for audit logs — read-only.
    No delete action available.
    """
    list_display = [
        'timestamp', 'event_type', 'actor', 'actor_role',
        'organisation', 'work_record', 'before_state', 'after_state',
    ]
    list_filter = ['event_type', 'actor_role', 'timestamp']
    search_fields = ['actor__email', 'event_type', 'request_id']
    readonly_fields = [
        'id', 'timestamp', 'actor', 'actor_role', 'organisation',
        'event_type', 'work_record', 'before_state', 'after_state',
        'metadata', 'ip_address', 'user_agent', 'request_id',
    ]
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
