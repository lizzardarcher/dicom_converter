from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.text import slugify

from .models import Research, GlobalSettings, UserSettings, Transaction, User

admin.site.unregister(Group)
admin.site.unregister(User)


@admin.register(Research)
class ResearchAdmin(admin.ModelAdmin):
    list_display = ('user', 'date_created', 'raw_archive', 'is_anonymous', 'ready_archive', 'slug')
    list_filter = ('date_created', 'is_anonymous')
    search_fields = ('user__username', 'slug')
    readonly_fields = ('slug', 'date_created', 'ready_archive',)

    def save_model(self, request, obj, form, change):
        if not obj.slug:
            obj.slug = slugify(f'{obj.user} {str(obj.date_created)}')
        super().save_model(request, obj, form, change)


@admin.register(GlobalSettings)
class GlobalSettingsAdmin(admin.ModelAdmin):
    list_display = ('yookassa_api_key', 'yookassa_shop_id')

    def has_add_permission(self, request):
        if not GlobalSettings.objects.exists():
            return True
        else:
            return False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    class UserSettingsInline(admin.StackedInline):
        model = UserSettings
        can_delete = False
        verbose_name_plural = 'User Settings'

    class TransactionInline(admin.StackedInline):
        model = Transaction
        can_delete = False
        extra = 0
        verbose_name_plural = 'Transactions'

    inlines = (UserSettingsInline, TransactionInline)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'currency', 'timestamp')
