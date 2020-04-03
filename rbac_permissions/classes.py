from rest_framework import permissions

from django.conf import settings

from .constants import DEFAULT_ROLE_RULE_DENIED_ACCESS_MESSAGE
from .helpers import is_user_permitted


class GroupPermission(permissions.BasePermission):
    """A Permission class, which checks the role authorization of a user."""

    message = 'Only this group is allowed'
    groups_required = None

    def has_permission(self, request, view):
        """Overriden method, which checks role authorization of the user.

        Args:
            request (Request): the current request object
            view (View): the current View object

        Returns:
            (bool): True if the user is granted access.
        """

        # allow all access if the user is a superuser
        is_permitted = False
        is_group_in_tree = False

        if request.user.is_superuser:
            return True

        # prepare the url name
        url_name = request.resolver_match.url_name

        # for each group required, check if the current user is
        # senior / junior or equivalent to this required group within the
        # hierarchy
        for group_required in self.groups_required:
            # is_in_tree means that the user group / role is within the
            # required group / role tree (parent - child or equivalent)
            user_permitted, is_in_tree = is_user_permitted(
                request.user,
                group_required,
                url_name,
                request.method.lower()
            )
            is_permitted |= user_permitted
            is_group_in_tree |= is_in_tree

        if is_group_in_tree and not is_permitted:
            message = getattr(
                settings,
                'ROLE_RULE_DENIED_ACCESS_MESSAGE',
                DEFAULT_ROLE_RULE_DENIED_ACCESS_MESSAGE
            )
            self.message = message
        return is_permitted


# Mixins
class MultiplePermissionsMixin(object):
    """A mixin class which enables conditional permission checks."""

    def check_permissions(self, request):
        """Run has_permission for each permission class on the view."""
        exception_states = []
        permissions = self.get_permissions()

        all_groups = [group for permission in permissions
                      for group in permission.groups_required]

        for permission in permissions:
            if not permission.has_permission(request, self):
                permission_message_mappings = [
                    {
                        'role': role_name,
                        'message': permission.message
                    } for role_name in permission.groups_required
                ]
                exception_states.extend(permission_message_mappings)

        raise_permissions = len(exception_states) == len(all_groups)

        if raise_permissions:
            self.permission_denied(request, exception_states)
