from rest_framework import permissions

from .helpers import check_user_group_permission, is_in_group_tree

from .models import Transaction


class GroupPermission(permissions.BasePermission):
    message = 'Only this group is allowed'
    groups_required = None

    def has_permission(self, request, view):
        # allow all access if the user is a superuser
        is_permitted = False
        is_in_tree = False

        if request.user.is_superuser:
            return True

        # this will check the Groups tree to see if the current
        # user's group is a direct child of the given group, is parent of the
        # group or equal to the given group
        for group_required in self.groups_required:
            is_in_tree = is_in_group_tree(
                request.user, group_required)

            # it is a direct or indirect child so we need to check if this
            # user's group has this view's method permissions.
            if is_in_tree:
                url_name = request.resolver_match.url_name
                transaction = Transaction.objects.filter(
                    paths__icontains=url_name
                ).last()
                if not transaction:
                    continue

                permission_name = transaction.name

                # the format is: (basename of the routed url_method name)
                matching_permission = check_user_group_permission(
                    request.user, permission_name,
                    request.resolver_match.url_name,
                    request.method.lower(),
                )
                is_permitted |= matching_permission
            else:
                is_permitted |= False

        if is_in_tree and not is_permitted:
            self.message = (
                'You belong to the required role, '
                'but are not permitted to commit this transaction.'
            )

        return is_permitted


# Mixins
class MultiplePermissionsMixin(object):
    """
    A mixin class which enables conditional permission checks.
    """
    def check_permissions(self, request):
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
