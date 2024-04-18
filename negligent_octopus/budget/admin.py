from django.contrib import admin

from negligent_octopus.utils.admin import LimitedQuerysetInlineAdmin
from negligent_octopus.utils.admin import LimitedQuerysetInlineFormset

from .models import ImportActivo
from .models import ImportedActivoTransaction


class ImportedActivoTransactionInlineFormset(LimitedQuerysetInlineFormset):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs)[::-1]


class ImportedActivoTransactionInlineAdmin(LimitedQuerysetInlineAdmin):
    model = ImportedActivoTransaction
    fk_name = "loaded_from"
    fields = [
        "loaded_from",
        "date_of_movement",
        "date_of_process",
        "description",
        "value",
        "balance",
        "validated",
        "transaction",
    ]
    extra = 0
    formset = ImportedActivoTransactionInlineFormset


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
    inlines = [ImportedActivoTransactionInlineAdmin]

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


@admin.register(ImportedActivoTransaction)
class ImportedActivoTransactionAdmin(admin.ModelAdmin):
    fields = [
        "loaded_from",
        "date_of_movement",
        "date_of_process",
        "description",
        "value",
        "balance",
        "validated",
        "transaction",
    ]
    list_display = [
        "get_load_owner",
        "date_of_movement",
        "date_of_process",
        "description",
        "value",
        "balance",
        "validated",
        "has_transaction",
    ]
    list_display_links = ["description"]
    search_fields = [
        "description",
        "value",
        "balance",
    ]
    list_filter = [
        "loaded_from__owner",
        "date_of_movement",
        "date_of_process",
        "validated",
    ]
    readonly_fields = ["loaded_from"]

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.validated and obj.transaction is not None:
            return [
                *self.readonly_fields,
                "date_of_movement",
                "date_of_process",
                "description",
                "value",
                "balance",
                "validated",
                "transaction",
            ]
        return self.readonly_fields
