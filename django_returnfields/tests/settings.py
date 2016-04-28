import rest_framework
import os.path

DEBUG = True
SECRET_KEY = "test"
ROOT_URLCONF = "django_returnfields.tests.urls"
ALLOWED_HOSTS = ['*']
STATIC_URL = '/static/'
STATIC_ROOT = os.path.abspath(os.path.join(rest_framework.__path__[0], 'static'))
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    "rest_framework",
    __name__,
]
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
)
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASS": [
        "rest_framework.permissions.AllowAny"
    ]
}
DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": ":memory:"
}}
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
