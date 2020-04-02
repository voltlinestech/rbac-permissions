# Django RBAC Permissions

A Django package which enables RBAC with hierarchy and constraints enabled.

Quick Start
-----------

1. Add ```django_rbac_permissions``` to your INSTALLED_APPS setting like this:
   ```python
   INSTALLED_APPS = [
        ...
        'django_rbac_permissions',
        'django_json_widget'  # Optional
   ]
	  ```
  
   If you want to see your JSONFields in a pretty widget, include 
   ```django_json_widget``` in your INSTALLED_APPS as well.

2. Run ```python manage.py migrate``` to create the models.

3. If you want to define your modules (applications) in which you have
   resources which should check for role authorization, you must define
   a module configuration model. Ex:
   ```python
   class RoleModuleConfiguration(models.Model):
         posts = models.BooleanField(default=True)
         users = models.BooleanField(default=True)
         role_name = models.CharField(max_length=255)
   ```
   
   Each BooleanField symbolizes a module (application) and decides whether
   the given role_name is authorized to access it.

   You must also set ```MODULE_CONFIGURATION_PATH``` as the path, in which your model is residing.

4. If you also want to control the authorization in your admin page, you must
   add the middleware class ```CheckAdminRoleAuthorizationMiddleware``` to your
   MIDDLEWARE configuration in your Django settings file:
   ```python
    MIDDLEWARE = [
    ...
    'rbac_permissions.middleware.CheckAdminRoleAuthorizationMiddleware'
    ]
   ```
5. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a Role or Transaction.

