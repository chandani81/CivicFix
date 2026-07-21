from django.contrib import admin

from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "contact_email", "is_active"]
    list_filter = ["is_active", "category"]
    search_fields = ["name"]
