from django.contrib import admin
from django.utils.text import slugify

from .models import Research

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
