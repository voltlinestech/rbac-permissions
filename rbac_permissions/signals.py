from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Group, Permission
from django.utils.module_loading import import_string


def role_pre_save_actions(instance):
    """
    Creates a Group with the same name as the saved Role instance.

    Args:
        instance (Role): a Role instance.
    """

    group, created = Group.objects.get_or_create(name=instance.name)
    if created:
        instance.group_ptr = group


def role_post_save_actions(instance, created):
    """
    Fetches the module level permissions if defined within the wrapping app.
    Also inherits the parent's permissions, if the saved Role instance
    has any parent or parents.

    Args:
        instance (Role): a Role instance.
        created (bool): True if the instance is newly created.
    """

    from .models import RoleMembership, Transaction

    if not created:
        return

    # If the wrapping app defined any module configuration model, get it
    MODULE_CONFIGURATION_PATH = getattr(
        settings, 'MODULE_CONFIGURATION_PATH', None)
    parent = instance.parent
    granted_modules = []

    try:
        ModuleConfiguration = import_string(MODULE_CONFIGURATION_PATH)
        # Get related module permissions granted for the role
        # Get parent's granted modules as well so that we inherit them
        parent_role_name = instance.parent.name if instance.parent else None
        module_configurations = ModuleConfiguration.objects.filter(
            role_name__in=[instance.name, parent_role_name])
        # get all assigned modules for both the parent and the current role
        module_names = [
            module_name
            for module_configuration in module_configurations
            for module_name, value in module_configuration.__dict__.items()
            if value is True
        ]
        granted_modules.extend(module_names)
        # add any other module level parent permissions which are not stated
        # in your module configuration model
        if parent:
            granted_modules.extend(
                list(parent.permission_set.values_list('codename', flat=True))
            )
    except ImportError:
        pass

    # assign all the parent permissions
    # these are Django's default object level permissions
    if parent:
        granted_permissions = parent.permissions.all()
        group_ptr = instance.group_ptr
        group_ptr.permissions.set(granted_permissions)
        group_ptr.save()

    # prepare the final distinct module name set
    granted_modules = set(granted_modules)
    # get a random ContentType since we don't need it
    content_type = ContentType.objects.last()
    # assign all granted permissions by either creating or getting them
    for module_name in granted_modules:
        permission, _ = Permission.objects.get_or_create(
            codename=module_name,
            defaults={
                'name': 'Can view {}'.format(module_name),
                'content_type': content_type
            }
        )
        # get allowed transactions if any
        transaction, _ = Transaction.objects.get_or_create(
            name=module_name)
        RoleMembership.objects.create(
            permission=permission, role=instance, transaction=transaction
        )
    instance.save()
