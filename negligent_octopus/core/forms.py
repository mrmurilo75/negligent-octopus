from django import forms
from django.contrib.auth import get_user_model

from .models import Account
from .models import Transaction


class BaseForm(forms.ModelForm):
    def _override_field_queryset(self, field_name, model_class, filter_kwargs):
        field = self.fields.get(field_name, None)
        if field is not None:
            field.queryset = model_class.objects.filter(**filter_kwargs)


class AccountForm(BaseForm):
    owner = forms.ModelChoiceField(
        widget=forms.HiddenInput(),
        required=False,
        queryset=get_user_model().objects.none(),
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        if instance is not None:
            self._override_field_queryset(
                "owner",
                get_user_model(),
                {"pk": instance.owner.id},
            )

    class Meta:
        model = Account
        fields = "__all__"  # noqa: DJ007


class TransactionForm(BaseForm):
    account = forms.ModelChoiceField(
        queryset=Account.objects.none(),
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )
    destination_account = forms.ModelChoiceField(
        required=False,
        queryset=Account.objects.none(),
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )
    transfer_transaction = forms.ModelChoiceField(
        required=False,
        queryset=Transaction.objects.none(),
        # WARNING: Set it in view. Prevents user from selecting something not his.
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get("instance", None)
        if instance is not None:
            self._override_field_queryset(
                "account",
                Account,
                {"owner": instance.account.owner},
            )
            self._override_field_queryset(
                "destination_account",
                Account,
                {"owner": instance.account.owner},
            )
            self._override_field_queryset(
                "transfer_transaction",
                Transaction,
                {"account__owner": instance.account.owner},
            )

    class Meta:
        model = Transaction
        fields = "__all__"  # noqa: DJ007
