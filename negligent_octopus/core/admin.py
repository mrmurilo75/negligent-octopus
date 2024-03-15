from django.contrib import admin

from .models import Account
from .models import Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "balance", "modified", "created", "is_removed"]
    search_fields = ["name", "owner__username"]
    list_filter = [
        "owner",
        "is_removed",
        "modified",
    ]  # TODO: Check modified catches transaction changes


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["title", "account", "get_account_owner", "amount", "timestamp"]
    search_fields = ["account__owner__username", "account__name", "title"]
    list_filter = ["account__owner", "account", "timestamp"]
