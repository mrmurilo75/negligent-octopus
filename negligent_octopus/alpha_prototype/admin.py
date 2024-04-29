from django.contrib.admin.sites import AdminSite

from negligent_octopus.budget.admin import ImportActivoAdmin  # noqa: F401
from negligent_octopus.budget.admin import ImportedActivoTransactionAdmin  # noqa: F401
from negligent_octopus.budget.models import ImportActivo  # noqa: F401
from negligent_octopus.budget.models import ImportedActivoTransaction  # noqa: F401
from negligent_octopus.core.admin import AccountAdmin
from negligent_octopus.core.admin import CategoryAdmin  # noqa: F401
from negligent_octopus.core.admin import TransactionAdmin  # noqa: F401
from negligent_octopus.core.models import Account
from negligent_octopus.core.models import Category  # noqa: F401
from negligent_octopus.core.models import Transaction  # noqa: F401


class UserAdmin(AdminSite):
    # TODO Anything we wish to add or override

    def has_permission(self, request):
        return request.user.is_active


alpha_admin_site = UserAdmin(name="alpha_prototype")


class OpenAccountAdmin(AccountAdmin):
    # TODO Define permissions and filter by request.user
    pass


alpha_admin_site.register(Account, OpenAccountAdmin)
# TODO Apply same pattern for other classes (removed noqa once done)
