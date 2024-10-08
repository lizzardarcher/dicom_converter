from django.contrib import admin

from apps.home.models import Log

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False