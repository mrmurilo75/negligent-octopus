from django.contrib.admin.sites import AdminSite


class UserAdmin(AdminSite):
    # TODO Anything we wish to add or override
    pass


alpha_admin_site = UserAdmin(name="alpha_prototype")
