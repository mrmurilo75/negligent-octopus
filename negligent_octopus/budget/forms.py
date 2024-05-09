from django import forms
from django.contrib.auth import get_user_model

from negligent_octopus.core.models import Transaction
from negligent_octopus.utils.forms import ExtendedModelForm

from .models import SimpleImportedTransaction
from .models import SimpleTransactionsImport


class SimpleTransactionsImportForm(ExtendedModelForm):
    owner = forms.ModelChoiceField(
        widget=forms.HiddenInput(),
        required=False,
        queryset=None,
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )
    account = forms.ModelChoiceField(
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
            self.limit_field_queryset(
                "account",
                get_user_model(),
                {"account__owner": instance.owner.id},
            )

    class Meta:
        model = SimpleImportedTransaction
        fields = "__all__"


class SimpleImportedTransactionForm(ExtendedModelForm):
    loaded_from = forms.ModelChoiceField(
        required=False,
        queryset=None,
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )
    transaction = forms.ModelChoiceField(
        required=False,
        queryset=None,
        # Only show options on change
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        if instance is not None:
            self.limit_field_queryset(
                "loaded_from",
                SimpleTransactionsImport,
                {"loaded_from__owner": instance.loaded_from.owner},
            )
            self.limit_field_queryset(
                "transaction",
                Transaction,
                {"loaded_from__account": instance.loaded_from.account},
            )

    class Meta:
        model = SimpleImportedTransaction
        fields = "__all__"
