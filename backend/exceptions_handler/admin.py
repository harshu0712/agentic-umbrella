from django.contrib import admin
from exceptions_handler.models import PlatformException, ExceptionComment


class ExceptionCommentInline(admin.TabularInline):
    model = ExceptionComment
    extra = 0
    readonly_fields = ['id', 'author', 'message', 'created_at']


@admin.register(PlatformException)
class PlatformExceptionAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'exception_type', 'severity', 'status',
        'assigned_to', 'work_record', 'created_at', 'resolved_at',
    ]
    list_filter = ['status', 'severity', 'exception_type']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at', 'resolved_at']
    inlines = [ExceptionCommentInline]
