from django.contrib import admin
from django.forms import BaseInlineFormSet

from .models import Account
from .models import Transaction


class TransactionInlineFormset(BaseInlineFormSet):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).reverse()[: self.limit_queryset]


class TransactionInlineAdmin(admin.StackedInline):
    model = Transaction
    fk_name = "account"
    fieldsets = [
        (None, {"fields": ["title", "amount"]}),
        (
            "Details",
            {
                "classes": ["collapse"],
                "fields": ["timestamp", "description", "balance"],
            },
        ),
    ]
    readonly_fields = ["balance"]
    extra = 0
    formset = TransactionInlineFormset
    limit_queryset = 10

    def get_formset(self, *args, **kwargs):
        fs = super().get_formset(*args, **kwargs)
        fs.limit_queryset = self.limit_queryset
        return fs


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    fields = ["name", "owner", "initial_balance", "balance"]
    list_display = ["name", "owner", "balance", "created", "is_removed"]
    search_fields = ["name", "owner__username"]
    list_filter = [
        "owner",
        "is_removed",
    ]
    readonly_fields = ["balance"]
    inlines = [TransactionInlineAdmin]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["account", "title", "amount", "timestamp"]}),
        (
            "Details",
            {
                "classes": ["collapse"],
                "fields": ["description", "balance"],
            },
        ),
    ]
    readonly_fields = ["balance"]
    list_display = [
        "get_account_owner",
        "account",
        "title",
        "amount",
        "timestamp",
        "balance",
    ]
    list_display_links = ["title"]
    search_fields = ["account__owner__username", "account__name", "title"]
    list_filter = ["account__owner", "account", "timestamp"]
