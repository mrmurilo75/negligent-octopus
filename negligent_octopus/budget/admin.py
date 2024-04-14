from django.contrib import admin

from .models import LoadActivo


@admin.register(LoadActivo)
class LoadActivoAdmin(admin.ModelAdmin):
    fields = ["created", "owner", "is_removed"]
    list_display = ["name", "owner"]
    search_fields = ["name", "owner__username"]
    list_filter = [
        "owner",
        "is_removed",
    ]
