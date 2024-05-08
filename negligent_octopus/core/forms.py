from django import forms

from .models import Account
from .models import Transaction


class AccountForm(forms.ModelForm):
    owner = forms.ModelChoiceField(
        widget=forms.HiddenInput(),
        required=False,
        queryset=None,
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )

    class Meta:
        model = Account
        fields = "__all__"  # noqa: DJ007


class TransactionForm(forms.ModelForm):
    account = forms.ModelChoiceField(
        queryset=None,
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )
    destination_account = forms.ModelChoiceField(
        queryset=None,
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )
    transfer_transaction = forms.ModelChoiceField(
        queryset=None,
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )

    class Meta:
        model = Transaction
        fields = "__all__"  # noqa: DJ007
