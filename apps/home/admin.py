from django.contrib import admin

from apps.home.models import Log

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('user', 'level', 'created_at', 'short_message')
    list_filter = ('level', 'created_at')
    search_fields = ('message', 'user__username')
    readonly_fields = ('user', 'level', 'created_at', 'message')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 25

    @admin.display(description='Сообщение')
    def short_message(self, obj):
        if obj.message and len(obj.message) > 80:
            return f'{obj.message[:80]}…'
        return obj.message

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
