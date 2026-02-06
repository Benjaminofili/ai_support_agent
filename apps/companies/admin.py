from django.contrib import admin

from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "owner", "created_at"]
    search_fields = ["name", "slug"]
    readonly_fields = ["id", "api_key", "created_at", "updated_at"]
