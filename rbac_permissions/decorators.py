import functools

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse

from .constants import (
    DEFAULT_HTTP_FORBIDDEN_MESSAGE,
    DEFAULT_ROLE_RULE_DENIED_ACCESS_MESSAGE,
    DEFAULT_PERMISSION_DENIED_URL
)
from .helpers import is_user_permitted


ROLE_RULE_DENIED_ACCESS_MESSAGE = getattr(
    settings, 'ROLE_RULE_DENIED_ACCESS_MESSAGE',
    DEFAULT_ROLE_RULE_DENIED_ACCESS_MESSAGE
)
HTTP_FORBIDDEN_MESSAGE = getattr(
    settings, 'HTTP_FORBIDDEN_MESSAGE', DEFAULT_HTTP_FORBIDDEN_MESSAGE
)

PERMISSION_DENIED_URL = getattr(
    settings, 'PERMISSION_DENIED_URL', DEFAULT_PERMISSION_DENIED_URL
)


def user_groups_required(groups_required=None):
    """
    A decorator to be used in functional views, which checks the current user
    groups / roles and determines whether to grant access to this user.
    """
    def decorator(view_func, groups_required=None):
        def wrapper(*args, **kwargs):
            is_permitted = False
            is_group_in_tree = False
            # get the request object from args
            request = args[0]
            # prepare the url name
            url_name = request.resolver_match.url_name
            # get the passed required user group/role names
            groups_required = kwargs.pop('groups_required')

            # for each group required, check if the current user is
            # senior / junior or equivalent to this required group within the
            # hierarchy
            for group_required in groups_required:
                user_permitted, is_in_tree = is_user_permitted(
                    request.user, group_required, url_name,
                    request.method.lower())
                is_permitted |= user_permitted
                is_group_in_tree |= is_in_tree

            if not is_permitted:
                if is_group_in_tree:
                    message = ROLE_RULE_DENIED_ACCESS_MESSAGE
                else:
                    message = HTTP_FORBIDDEN_MESSAGE

                url_name = PERMISSION_DENIED_URL
                url = reverse(url_name) + '?message={}'.format(message)
                # redirect to the defined permission denied view
                return HttpResponseRedirect(url)
            return view_func(*args, **kwargs)
        return functools.partial(wrapper, groups_required=groups_required)
    return functools.partial(decorator, groups_required=groups_required)
