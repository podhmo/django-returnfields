import os.path
import copy
import importlib
import argparse
from django.db import connections
from django.test.client import Client


default_settings = dict(
    DEBUG=True,
    ALLOWED_HOSTS=['*'],
    INSTALLED_APPS=[
        "django.contrib.staticfiles",
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "rest_framework",
    ],
    STATIC_URL='/static/',
    MIDDLEWARE_CLASSES=(
        'django.middleware.common.CommonMiddleware',
    ),
    REST_FRAMEWORK={
        "DEFAULT_PERMISSION_CLASS": [
            "rest_framework.permissions.AllowAny"
        ]
    },
    DATABASES={"default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:"
    }},
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
)


def create_table(model, dbalias="default"):
    connection = connections[dbalias]
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)


def maybe_list(x):
    if isinstance(x, (list, tuple)):
        return x
    else:
        return [x]


class SettingsHandler(object):
    defaults = {
        "settings": default_settings,
        "STATIC_ROOT": None,
        "dbalias": "default"
    }

    def get_settings_options(self, root_urlconf):
        options = copy.copy(self.defaults["settings"])
        options.update(
            STATIC_ROOT=self.defaults["STATIC_ROOT"] or self.get_static_root(),
            ROOT_URLCONF=root_urlconf
        )
        return options

    def get_static_root(self):
        import rest_framework
        return os.path.abspath(os.path.join(rest_framework.__path__[0], 'static'))


class App(object):
    def __init__(self, settings_handler=SettingsHandler()):
        self.settings_handler = settings_handler

    def setup(self, apps, root_urlconf, extra_settings=None):
        import django
        from django.conf import settings
        apps = maybe_list(apps)
        options = self.settings_handler.get_settings_options(root_urlconf)
        options["INSTALLED_APPS"].extend(apps)
        if extra_settings:
            options.update(extra_settings)
        settings.configure(**options)
        django.setup()

    def setup_urlconf(self, router):
        # url
        from django.conf.urls import url, include
        from django.contrib.staticfiles.urls import staticfiles_urlpatterns

        urlpatterns = [
            url(r'^', include(router.urls))
        ]
        urlpatterns += staticfiles_urlpatterns()
        return urlpatterns

    def load_module(self, module_name):
        return importlib.import_module(module_name)

    def run(self, main_client):
        parser = self.create_arg_parser()
        args = parser.parse_args()

        if args.run_server:
            self.run_server(port=8080)
        else:
            self.run_client(main_client)

    def run_server(self, port=8000):
        from django.core.management.commands.runserver import Command
        return Command().execute(addrport=str(port))

    def run_client(self, callback):
        client = Client()
        return callback(client)

    def create_arg_parser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--run-server", dest="run_server", action="store_true", default=False)
        return parser

    def create_table(self, *models):
        for model in models:
            create_table(model, dbalias=self.settings_handler.defaults["dbalias"])
