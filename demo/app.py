# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
from django.conf import settings
import os.path
import rest_framework


settings.configure(
    DEBUG=True,
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=['*'],
    INSTALLED_APPS=[
        "django.contrib.staticfiles",
        "django.contrib.contenttypes",
        "django.contrib.auth",
        "rest_framework",
        __name__,
    ],
    STATIC_URL='/static/',
    STATIC_ROOT=os.path.abspath(os.path.join(rest_framework.__path__[0], 'static')),
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
import django
django.setup()


from django.db import connections
from django.core.management.color import no_style
from rest_framework import routers, serializers, viewsets
from django.db import models
from django_returnfields import serializer_factory  # this!!


def create_table(model):
    connection = connections['default']
    if hasattr(connection, "schema_editor"):
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(model)
    else:
        cursor = connection.cursor()
        sql, references = connection.creation.sql_create_model(model, no_style())
        for statement in sql:
            cursor.execute(statement)

        for f in model._meta.many_to_many:
            create_table(f.rel.through)


# models
from django.contrib.auth.models import User


class Skill(models.Model):
    name = models.CharField(max_length=255, default="", null=False)
    user = models.ForeignKey(User, null=False, related_name="skills")

    class Meta:
        app_label = __name__


# serializers
class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'user', 'name')


class UserSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'is_staff', 'skills')


# viewsets
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializer_factory(UserSerializer)


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = serializer_factory(SkillSerializer)


# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'skills', SkillViewSet)

# url
from django.conf.urls import url, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    url(r'^', include(router.urls))
]
urlpatterns += staticfiles_urlpatterns()


def main_client():
    """call view via Client"""
    import json
    from django.test.client import Client
    client = Client()

    # success request
    path = "/users/"
    print("========================================")
    print("request: GET {}".format(path))
    response = client.get(path)
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))

    path = "/users/"
    print("========================================")
    print("request: POST {}".format(path))
    response = client.post(path, {"username": "foo"})
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))
    path = "/skills/"

    print("========================================")
    print("request: POST {}".format(path))
    response = client.post(path, {"user": 1, "name": "magic"})
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))
    print("========================================")
    print("request: POST {}".format(path))
    response = client.post(path, {"user": 1, "name": "magik"})
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))

    path = "/users/1/?format=json"
    response = client.get(path)
    print("========================================")
    print("request: GET {}".format(path))
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))

    path = "/users/1/?format=json&return_fields=username,id"
    response = client.get(path)
    print("========================================")
    print("request: GET {}".format(path))
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))

    path = "/users/1/?format=json&return_fields=username,skills&skip_fields=skills__id,skills__user"
    response = client.get(path)
    print("========================================")
    print("request: GET {}".format(path))
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))


def main_run_server():
    """runserver localhost:8000"""
    from django.core.management.commands.runserver import Command
    Command().execute()

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-server", dest="run_server", action="store_true", default=False)
    args = parser.parse_args(sys.argv[1:])

    create_table(User)
    create_table(Skill)

    if args.run_server:
        main_run_server()
    else:
        main_client()
