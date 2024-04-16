from django.contrib import admin

from .models import ImportActivo


@admin.register(ImportActivo)
class ImportActivoAdmin(admin.ModelAdmin):
    list_display = ["owner", "name", "account", "processed", "created"]
    list_display_links = ["name"]
    search_fields = ["name", "account__name", "owner__name"]
    list_filter = [
        "owner",
        "account",
        "processed",
        "created",
    ]

    def get_readonly_fields(
        self,
        request,
        obj: ImportActivo | None = None,
    ):
        if obj is None:
            return self.readonly_fields
        readonly_fields = [*self.readonly_fields, "load"]
        if obj.processed:
            readonly_fields += ["account", "processed"]
        return readonly_fields
