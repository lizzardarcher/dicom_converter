from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.text import slugify

from .models import Research, GlobalSettings, UserSettings, User, TestResearch

admin.site.unregister(Group)
admin.site.unregister(User)

@admin.register(Research)
class ResearchAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_created', 'raw_archive', 'ready_archive', 'slug')
    list_filter = ('date_created', 'is_anonymous')
    search_fields = ('user__username', 'slug')
    readonly_fields = ('slug', 'date_created', 'ready_archive',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True

    def save_model(self, request, obj, form, change):
        if not obj.slug:
            obj.slug = slugify(f'{obj.user} {str(obj.date_created)}')
        super().save_model(request, obj, form, change)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    class UserSettingsInline(admin.StackedInline):
        model = UserSettings
        can_delete = False
        verbose_name_plural = 'User Settings'

    inlines = (UserSettingsInline, )


@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False