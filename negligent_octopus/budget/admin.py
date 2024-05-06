from django.contrib import admin

from negligent_octopus.utils.admin import LimitedQuerysetInlineAdmin
from negligent_octopus.utils.admin import LimitedQuerysetInlineFormset

from .models import SimpleImportedTransaction
from .models import SimpleTransactionsImport


class SimpleImportedTransactionInlineFormset(LimitedQuerysetInlineFormset):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs)[::-1]


class SimpleImportedTransactionInlineAdmin(LimitedQuerysetInlineAdmin):
    model = SimpleImportedTransaction
    fk_name = "loaded_from"
    fields = [
        "loaded_from",
        "date",
        "title",
        "amount",
        "balance",
        "validated",
        "transaction",
    ]
    extra = 0
    formset = SimpleImportedTransactionInlineFormset


@admin.register(SimpleTransactionsImport)
class SimpleTransactionsImportAdmin(admin.ModelAdmin):
    list_display = ["owner", "name", "account", "processed", "created"]
    list_display_links = ["name"]
    search_fields = ["name", "account__name", "owner__name"]
    list_filter = [
        "owner",
        "account",
        "processed",
        "created",
    ]
    inlines = [SimpleImportedTransactionInlineAdmin]

    def get_inlines(self, request, obj):
        if obj is None:
            return ()
        return super().get_inlines(request, obj)

    def get_readonly_fields(
        self,
        request,
        obj=None,
    ):
        if obj is None:
            return self.readonly_fields
        readonly_fields = [*self.readonly_fields, "load", "processed"]
        if obj.processed:
            readonly_fields += ["account"]
        return readonly_fields


@admin.register(SimpleImportedTransaction)
class SimpleImportedTransactionAdmin(admin.ModelAdmin):
    fields = [
        "loaded_from",
        "date",
        "title",
        "amount",
        "balance",
        "validated",
        "transaction",
    ]
    list_display = [
        "get_load_owner",
        "date",
        "title",
        "amount",
        "balance",
        "validated",
        "has_transaction",
    ]
    list_display_links = ["title"]
    search_fields = [
        "title",
        "amount",
        "balance",
    ]
    list_filter = [
        "loaded_from__owner",
        "date",
        "validated",
    ]
    readonly_fields = ["loaded_from"]

    def get_readonly_fields(self, request, obj=None):
        if obj is not None and obj.validated and obj.transaction is not None:
            return [
                *self.readonly_fields,
                "date",
                "title",
                "amount",
                "balance",
                "validated",
                "transaction",
            ]
        return self.readonly_fields
