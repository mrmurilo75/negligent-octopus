from django import forms
from django.contrib.auth import get_user_model

from negligent_octopus.utils.forms import ExtendedModelForm

from .models import Account
from .models import Transaction


class AccountForm(ExtendedModelForm):
    owner = forms.ModelChoiceField(
        widget=forms.HiddenInput(),
        required=False,
        queryset=None,
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        if instance is not None:
            self.limit_field_queryset(
                "owner",
                get_user_model(),
                {"pk": instance.owner.id},
            )

    class Meta:
        model = Account
        fields = "__all__"


class TransactionForm(ExtendedModelForm):
    account = forms.ModelChoiceField(
        queryset=None,
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )
    destination_account = forms.ModelChoiceField(
        required=False,
        queryset=None,
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )
    transfer_transaction = forms.ModelChoiceField(
        required=False,
        queryset=None,
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        if instance is not None:
            self.limit_field_queryset(
                "account",
                Account,
                {"owner": instance.account.owner},
            )
            self.limit_field_queryset(
                "destination_account",
                Account,
                {"owner": instance.account.owner},
            )
            self.limit_field_queryset(
                "transfer_transaction",
                Transaction,
                {"account__owner": instance.account.owner},
            )

    class Meta:
        model = Transaction
        fields = "__all__"
