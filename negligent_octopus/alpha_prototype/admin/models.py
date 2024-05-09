from django.contrib.auth import get_user_model

from negligent_octopus.budget.admin import SimpleImportedTransactionAdmin
from negligent_octopus.budget.admin import SimpleTransactionsImportAdmin
from negligent_octopus.budget.forms import SimpleImportedTransactionForm
from negligent_octopus.budget.forms import SimpleTransactionsImportForm
from negligent_octopus.budget.models import SimpleImportedTransaction
from negligent_octopus.budget.models import SimpleTransactionsImport
from negligent_octopus.core.admin import AccountAdmin
from negligent_octopus.core.admin import CategoryAdmin
from negligent_octopus.core.admin import TransactionAdmin
from negligent_octopus.core.forms import AccountForm
from negligent_octopus.core.forms import TransactionForm
from negligent_octopus.core.models import Account
from negligent_octopus.core.models import Category
from negligent_octopus.core.models import Transaction

from .site import alpha_admin_site


class BaseOpenAdmin:
    user_relation_field = "owner"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(**{self.user_relation_field: request.user})


class OpenSimpleTransactionsImportAdmin(BaseOpenAdmin, SimpleTransactionsImportAdmin):
    form = SimpleTransactionsImportForm

    def save_form(self, request, form, change):
        form.instance.owner = get_user_model().objects.get(pk=request.user.id)
        return super().save_form(request, form, change)


class OpenSimpleImportedTransactionAdmin(BaseOpenAdmin, SimpleImportedTransactionAdmin):
    user_relation_field = "loaded_from__owner"
    form = SimpleImportedTransactionForm

    def get_form(self, request, *args, **kwargs):
        owner = get_user_model().objects.get(pk=request.user.id)
        self.form.declared_fields[
            "loaded_from"
        ].queryset = SimpleTransactionsImport.objects.filter(owner=owner)
        return super().get_form(request, *args, **kwargs)


class OpenCategoryAdmin(BaseOpenAdmin, CategoryAdmin):
    pass


class OpenTransactionAdmin(BaseOpenAdmin, TransactionAdmin):
    user_relation_field = "account__owner"
    form = TransactionForm

    def get_form(self, request, *args, **kwargs):
        owner = get_user_model().objects.get(pk=request.user.id)
        self.form.declared_fields["account"].queryset = Account.objects.filter(
            owner=owner,
        )
        self.form.declared_fields[
            "destination_account"
        ].queryset = Account.objects.filter(owner=owner)
        self.form.declared_fields[
            "transfer_transaction"
        ].queryset = Transaction.objects.filter(account__owner=owner)
        return super().get_form(request, *args, **kwargs)


class OpenAccountAdmin(BaseOpenAdmin, AccountAdmin):
    form = AccountForm

    def save_form(self, request, form, change):
        form.instance.owner = get_user_model().objects.get(pk=request.user.id)
        return super().save_form(request, form, change)


alpha_admin_site.register(SimpleTransactionsImport, OpenSimpleTransactionsImportAdmin)
alpha_admin_site.register(SimpleImportedTransaction, OpenSimpleImportedTransactionAdmin)
alpha_admin_site.register(Account, OpenAccountAdmin)
alpha_admin_site.register(Category, OpenCategoryAdmin)
alpha_admin_site.register(Transaction, OpenTransactionAdmin)
