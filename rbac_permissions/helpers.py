from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.urls.resolvers import RegexURLPattern

from .constants import (
    ALLOW_ALL_ROLES_SYMBOL,
    DEFAULT_ADMIN_URL as admin_url,
    DEFAULT_REQUEST_METHOD,
    DEFAULT_URLCONF as urlconf,
    DEFAULT_GRANT_NONEXISTENT_PATH_ACCESS,
    REQUEST_METHODS_TO_CRUD_OPERATIONS,
)
from .models import Transaction


def is_in_group_tree(user, group_name):
    """
    Checks if the given user's group is equal to group_name,
    is a parent of the group_name or a child of the group_name.

    If the given user's group is a parent of the group_name,
    this means that the user's group is junior to the given group_name.

    If the given user's group is a child of the group_name,
    this means that the user's group is senior to the given group_name.

    Args:
        user: A User instance.
        group_name: A string of a valid group name.

    Returns:
        is_in_group_tree (bool): whether the user group is connected
                                 to the given group within the tree.
    """

    is_parent = False
    is_child = False
    is_equal = False

    groups = user.groups.all()

    for group in groups:
        try:
            role = group.role
        except Group.role.RelatedObjectDoesNotExist:
            continue
        else:
            is_parent = group_name in (
                role.children.values_list('name', flat=True)
            )
            is_equal = role.name == group_name
            # is the user role the child of the required group
            is_child = role.parent.name == group_name if role.parent else False
            if is_parent or is_equal:
                break

    is_in_group_tree = any([is_child, is_equal])
    return is_in_group_tree


def check_user_group_permission(user, permission_name, resolved_path,
                                request_method=DEFAULT_REQUEST_METHOD):
    """
    Checks if the given user is granted the current transaction.

    Args:
        user (User): the current attempting user
        permission_name (str): the related transaction's permission name,
                         it is always related to a module. (offers, etc..)
        resolved_path (str): The basename of the resolved url
        request_method (str): The lowered current request method. (get, etc..)

    Returns:
        is_matching_permission (bool): Whether the user is granted the given
                                       permission (permission_name)
    """

    # if the user is an admin, don't bother to check other constraints
    if user.is_superuser:
        return True

    # try to get the permission, if it does not exist,
    # just return True since the group has all permissions
    # against a non existent permission.
    try:
        Permission.objects.get(codename=permission_name)
    except Permission.DoesNotExist:
        return True

    is_matching_permission = False
    groups = user.groups.all()

    # for each user group, get her role memberships
    # role memberships are permission holders, holding information about
    # allowed transactions of the role's related permission
    query = {'transaction__name': permission_name,
             'transaction__paths__contains': resolved_path}

    for group in groups:
        role = group.role
        role_membership = role.memberships.filter(**query).last()
        # if there is no related membership for this permission,
        # continue the iteration since we cannot be sure to grant the
        # permission
        if not role_membership:
            continue

        # check if the given role is permitted to apply the request method
        # here, we basically get the related transaction,
        # and check its rules to see if user's group match the current rule
        allowed_transaction = role_membership.transaction
        transaction_rule = allowed_transaction.rules.get(resolved_path)

        # if the rule is not defined for this url, temporarily grant the
        # permission
        # If the user has multiple groups, and the other group's role has
        # defined a transaction with rules associated with this url,
        # the succeeding block will work and decide to grant or not
        if not transaction_rule:
            is_matching_permission = True
            continue

        # Check if our user's role name is within the defined role's
        # in the request method's rule set
        allowed_roles = transaction_rule.get(
            REQUEST_METHODS_TO_CRUD_OPERATIONS.get(request_method)
        )
        is_matching_permission = (role.name in allowed_roles or
                                  ALLOW_ALL_ROLES_SYMBOL in allowed_roles)
        # break if a matching permission is found
        if is_matching_permission:
            break

    return is_matching_permission


def get_all_urls_with_names():
    """
    Gets all Django && user defined url names from the rool url configuration.

    The root url configuration resides in your app's 'urls.py', which is
    under the app's root folder.

    Returns:
        all_url_names (list): List of url names.
    """

    # fetch all the url patterns from your rool url configuration
    root_urlconf = __import__(getattr(settings, urlconf), {}, {}, [''])
    url_patterns = root_urlconf.urlpatterns
    all_url_names = []

    for pattern in url_patterns:
        if isinstance(pattern, RegexURLPattern):
            continue

        url_names = list(
            filter(lambda name: isinstance(name, str),
                   pattern.reverse_dict.keys())
        )
        all_url_names.extend(url_names)

    # add the base admin index url as well
    all_url_names.append(admin_url)

    return all_url_names


def is_user_permitted(user, group_required, url_name, method):
    """
    Check if the given user is permitted to access a resource, which can only
    be accessed by the group_required parameter.

    Args:
        user (User): a User instance.
        group_required (str): the group / role name that the user must hold
                              in order to access a resource.
        url_name (str): the name of the url. It is the resource to be accessed.
        method (str): the lowered request method.

    Returns:
        (tuple(bool, bool)): First boolean: whether the user is permitted
                             Second boolean: whether the user group / role
                                             is within the required group tree.
    """

    is_permitted = False
    is_in_tree = False

    if user.is_superuser:
        return True, True

    # this will check the Groups tree to see if the current
    # user's group is a direct child of the given group, is parent of the
    # group or equal to the given group
    is_in_tree = is_in_group_tree(user, group_required)

    # it is a direct or indirect child so we need to check if this
    # user's group has this view's method permissions.
    if is_in_tree:
        transaction = Transaction.objects.filter(
            paths__icontains=url_name
        ).last()
        # if the current url path does not belong to any transaction,
        # decide if this means that the access is not granted or
        # a nonexistent path should be granted all accesses.
        if not transaction:
            GRANT_NONEXISTENT_PATH_ACCESS = getattr(
                settings, 'GRANT_NONEXISTENT_PATH_ACCESS',
                DEFAULT_GRANT_NONEXISTENT_PATH_ACCESS
            )
            return GRANT_NONEXISTENT_PATH_ACCESS, GRANT_NONEXISTENT_PATH_ACCESS

        permission_name = transaction.name

        # the format is: (basename of the routed url_method name)
        matching_permission = check_user_group_permission(
            user,
            permission_name,
            url_name,
            method
        )
        is_permitted = matching_permission
    else:
        is_permitted = False

    return is_permitted, is_in_tree
