from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied
from django.utils.deprecation import MiddlewareMixin

from .constants import (
    DEFAULT_ADMIN_URL_NAME as admin_url_name,
    DEFAULT_ADMIN_PERMISSION_NAME as admin_permission_name
)
from .helpers import check_user_group_permission


class CheckAdminRoleAuthorizationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """
        Checks if the current user is permitted to access the admin home page.
        """
        is_permitted = True
        admin_index_path = reverse(admin_url_name)
        if request.path == admin_index_path:
            if request.user.is_authenticated():
                is_permitted = check_user_group_permission(
                    request.user,
                    admin_permission_name,
                    admin_index_path,
                    request.method.lower(),
                )
        if not is_permitted:
            raise PermissionDenied
