REQUEST_METHODS_TO_CRUD_OPERATIONS = {
    'get': 'read',
    'post': 'create',
    'put': 'update',
    'delete': 'delete'
}

DEFAULT_REQUEST_METHOD = 'get'
DEFAULT_URLCONF = 'ROOT_URLCONF'
DEFAULT_ADMIN_PERMISSION_NAME = 'admin'
DEFAULT_ADMIN_URL = '/admin/'
DEFAULT_ADMIN_URL_NAME = 'admin:index'
DEFAULT_PERMISSION_DENIED_URL = 'permission-denied'
# Determines whether to give access to a nonexistent path
# nonexistent path = a path which is not added to an existing Transaction
DEFAULT_GRANT_NONEXISTENT_PATH_ACCESS = False
# Messages
DEFAULT_HTTP_FORBIDDEN_MESSAGE = (
    'You are not allowed to commit this transaction.'
)
DEFAULT_ROLE_RULE_DENIED_ACCESS_MESSAGE = (
    'You belong to the required role, '
    'but are not permitted to commit this transaction.'
)

ALLOW_ALL_ROLES_SYMBOL = '*'

# Optional 3rd party package names
DJANGO_JSON_WIDGET = 'django_json_widget'
