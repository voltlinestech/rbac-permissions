# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django import forms

from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.postgres.fields import jsonb

from .constants import DJANGO_JSON_WIDGET
from .models import Role, Transaction, RoleMembership
from .helpers import get_all_urls_with_names


# Get the generic User model
User = get_user_model()
# Unregister the Group admin
admin.site.unregister(Group)


try:
    from django_json_widget import widgets
    JSONEditorWidget = widgets.JSONEditorWidget
except ImportError:
    JSONEditorWidget = forms.Textarea
finally:
    INSTALLED_APPS = getattr(settings, 'INSTALLED_APPS', None)
    if DJANGO_JSON_WIDGET not in INSTALLED_APPS:
        JSONEditorWidget = forms.Textarea


# Form classes
class RoleAdminForm(forms.ModelForm):
    class Meta:
        model = Role
        exclude = ()

    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('users', False)
    )

    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('permissions', False)
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['users'].initial = self.instance.user_set.all()
            self.fields['permissions'].initial = (
                self.instance.permissions.all()
            )

    def save_m2m(self):
        self.instance.user_set.set(self.cleaned_data['users'])

        cleaned_permissions = self.cleaned_data['permissions']

        if cleaned_permissions:
            self.instance.group_ptr.permissions.set(cleaned_permissions)
            # if has any children (senior roles), set permissions for them
            children = self.instance.children.all()
            for child in children:
                child.group_ptr.permissions.set(cleaned_permissions)

    def save(self, *args, **kwargs):
        instance = self.instance.save()
        self.save_m2m()
        return instance


class TransactionAdminForm(forms.ModelForm):
    paths = forms.MultipleChoiceField(
        choices=[],
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        all_url_names = get_all_urls_with_names()
        choices = [(name, name) for name in all_url_names]
        self.fields['paths'].choices = choices

    class Meta:
        model = Transaction
        exclude = ()


# Admin Classes
class RoleMembershipInline(admin.TabularInline):
    model = RoleMembership
    raw_id_fields = ('transaction', 'permission')


class RoleAdmin(admin.ModelAdmin):
    form = RoleAdminForm
    filter_horizontal = ['permission_set']
    list_display = ('name', )
    inlines = [RoleMembershipInline, ]


class TransactionAdmin(admin.ModelAdmin):
    formfield_overrides = {
        jsonb.JSONField: {
            'widget': JSONEditorWidget
        }
    }
    form = TransactionAdminForm

    def save_model(self, request, obj, form, change):
        if 'paths' in form.changed_data:
            db_instance = Transaction.objects.get(pk=obj.pk)
            added_paths = set(obj.paths) - set(db_instance.paths)

            rules_to_add = {
                path_name: {
                    'create': [],
                    'read': [],
                    'update': [],
                    'delete': []
                } for path_name in added_paths
            }
            rules = obj.rules
            if isinstance(rules, str):
                rules = rules.replace("\'", "\"")
                rules = json.loads(rules)
            updated_rules = {**rules, **rules_to_add}
            obj.rules = updated_rules
        super().save_model(request, obj, form, change)


admin.site.register(Role, RoleAdmin)
admin.site.register(Transaction, TransactionAdmin)
