from django.contrib import admin

from negligent_octopus.utils.admin import LimitedQuerysetInlineAdmin
from negligent_octopus.utils.admin import LimitedQuerysetInlineFormset

from .models import Account
from .models import Category
from .models import Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    fields = ["name", "owner"]
    list_display = ["name", "owner"]
    search_fields = ["name", "owner__username"]
    list_filter = ["owner"]


class TransactionInlineFormset(LimitedQuerysetInlineFormset):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs)[::-1]


class TransactionInlineAdmin(LimitedQuerysetInlineAdmin):
    model = Transaction
    fk_name = "account"
    fieldsets = [
        (None, {"fields": ["title", "amount", "category"]}),
        (
            "Details",
            {
                "classes": ["collapse"],
                "fields": ["timestamp", "description", "balance"],
            },
        ),
        (
            "Transfer",
            {
                "classes": ["collapse"],
                "fields": ["destination_account", "transfer_transaction"],
            },
        ),
    ]
    readonly_fields = ["balance", "transfer_transaction"]
    extra = 0
    formset = TransactionInlineFormset


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    fields = ["name", "owner", "initial_balance", "balance"]
    list_display = ["name", "owner", "balance", "created"]
    search_fields = ["name", "owner__username"]
    list_filter = ["owner"]
    readonly_fields = ["balance"]
    inlines = [TransactionInlineAdmin]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["account", "title", "amount"]}),
        (
            "Details",
            {
                "classes": ["collapse"],
                "fields": ["category", "timestamp", "description", "balance"],
            },
        ),
        (
            "Transfer",
            {
                "classes": ["collapse"],
                "fields": ["destination_account", "transfer_transaction"],
            },
        ),
    ]
    readonly_fields = ["balance", "transfer_transaction"]
    list_display = [
        "account_owner",
        "account",
        "title",
        "amount",
        "category",
        "timestamp",
        "balance",
        "is_transfer",
    ]
    list_display_links = ["title"]
    search_fields = [
        "account__owner__username",
        "account__name",
        "title",
        "category__name",
        "balance",
        "amount",
    ]
    list_filter = ["account__owner", "account", "category", "timestamp"]

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return self.readonly_fields
        return [*self.readonly_fields, "account"]
