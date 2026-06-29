from django.contrib import admin

from apps.payments.models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'description', 'status', 'paid', 'created_at')
    list_filter = ('status', 'paid', 'description', 'created_at')
    search_fields = ('user__username', 'payment_id')
    readonly_fields = (
        'amount', 'description', 'payment_id', 'created_at',
        'paid', 'status', 'currency', 'user',
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 25

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
