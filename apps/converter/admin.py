from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.text import slugify

from .models import Research, GlobalSettings, UserSettings, User


admin.site.unregister(Group)
admin.site.unregister(User)


@admin.register(Research)
class ResearchAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_created', 'status', 'is_anonymous', 'slug')
    list_filter = ('date_created', 'is_anonymous', 'status')
    search_fields = ('user__username', 'slug')
    readonly_fields = ('slug', 'date_created', 'ready_archive',)
    date_hierarchy = 'date_created'
    ordering = ('-date_created',)
    list_per_page = 25

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
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('is_staff', 'is_active', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 25

    class UserSettingsInline(admin.StackedInline):
        model = UserSettings
        can_delete = False
        verbose_name_plural = 'User Settings'

    inlines = (UserSettingsInline,)


@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'price_1_ru', 'price_2_ru', 'price_3_ru')

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
