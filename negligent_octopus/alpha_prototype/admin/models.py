from negligent_octopus.budget.admin import SimpleImportedTransactionAdmin
from negligent_octopus.budget.admin import SimpleTransactionsImportAdmin
from negligent_octopus.budget.models import SimpleImportedTransaction
from negligent_octopus.budget.models import SimpleTransactionsImport
from negligent_octopus.core.admin import AccountAdmin
from negligent_octopus.core.admin import CategoryAdmin
from negligent_octopus.core.admin import TransactionAdmin
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
    pass


class OpenSimpleImportedTransactionAdmin(BaseOpenAdmin, SimpleImportedTransactionAdmin):
    user_relation_field = "loaded_from__owner"


class OpenCategoryAdmin(BaseOpenAdmin, CategoryAdmin):
    pass


class OpenTransactionAdmin(BaseOpenAdmin, TransactionAdmin):
    user_relation_field = "account__owner"


class OpenAccountAdmin(BaseOpenAdmin, AccountAdmin):
    pass


alpha_admin_site.register(SimpleTransactionsImport, OpenSimpleTransactionsImportAdmin)
alpha_admin_site.register(SimpleImportedTransaction, OpenSimpleImportedTransactionAdmin)
alpha_admin_site.register(Account, OpenAccountAdmin)
alpha_admin_site.register(Category, OpenCategoryAdmin)
alpha_admin_site.register(Transaction, OpenTransactionAdmin)
