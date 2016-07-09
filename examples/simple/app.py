# -*- coding:utf-8 -*-
from django_returnfields.app import App  # shorthand

app = App()
app.setup(apps=[__name__], root_urlconf=__name__)

from rest_framework import routers, serializers, viewsets
from django.db import models
from django_returnfields import serializer_factory  # this!!

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
urlpatterns = app.setup_urlconf(router)


def main_client(client):
    """call view via Client"""
    import json

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


if __name__ == "__main__":
    app.create_table(User, Skill)
    app.run(main_client)
