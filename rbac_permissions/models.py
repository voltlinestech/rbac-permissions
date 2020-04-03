# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# TODO
from .fields import *  # noqa

from django.contrib.auth.models import Group, Permission
from django.contrib.postgres.fields import jsonb
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .signals import role_pre_save_actions, role_post_save_actions


class Transaction(models.Model):
    name = models.CharField(max_length=255, blank=False)
    paths = jsonb.JSONField(default=list, null=True, blank=True)
    rules = jsonb.JSONField(default=dict, null=True, blank=True)

    def __str__(self):
        return self.name


class RoleMembership(models.Model):
    permission = models.ForeignKey(Permission, related_name='memberships',
                                   on_delete=models.SET_NULL,
                                   null=True)
    role = models.ForeignKey('Role', related_name='memberships',
                             on_delete=models.SET_NULL, null=True)
    transaction = models.ForeignKey('Transaction', on_delete=models.SET_NULL,
                                    null=True)

    def __str__(self):
        role_name = self.role.name if self.role else None
        permission_name = self.permission.codename if self.permission else None
        return 'Role {} is a member of Permission {}'.format(role_name,
                                                             permission_name)


class Role(Group):
    parent = models.ForeignKey('self', blank=True, null=True,
                               related_name='children',
                               on_delete=models.CASCADE)
    permission_set = models.ManyToManyField(
        Permission, verbose_name=_('permissions'),
        through='RoleMembership', related_name='roles'
    )

    def save(self, *args, **kwargs):
        created = self.pk is None
        role_pre_save_actions(self)
        super().save()
        role_post_save_actions(self, created)
        return self
