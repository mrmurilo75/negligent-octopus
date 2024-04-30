from django.contrib.admin.sites import AdminSite


class UserAdmin(AdminSite):
    # TODO Anything we wish to add or override

    def has_permission(self, request):
        return request.user.is_active


alpha_admin_site = UserAdmin(name="alpha_prototype")
