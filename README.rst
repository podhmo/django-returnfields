django-returnfields
========================================

.. image:: https://travis-ci.org/podhmo/django-returnfields.svg
  :target: https://travis-ci.org/podhmo/django-returnfields.svg

adding restriction of your api's return fields, in restframework.

what is this?
----------------------------------------

The api is defined, such as below.

::

  request: GET /users/1/?format=json
  status code: 200
  response: {
    "id": 1,
    "url": "http://testserver/users/1/?format=json",
    "username": "foo",
    "email": "",
    "is_staff": false,
    "skills": [
      {
        "id": 1,
        "user": 1,
        "name": "magic"
      },
      {
        "id": 2,
        "user": 1,
        "name": "magik"
      }
    ]
  }

If you passing `return_fields` option, api's response is filtered.

::

  request: GET /users/1/?format=json&return_fields=username,id
  status code: 200
  response: {
    "id": 1,
    "username": "foo"
  }

And adding `skip__fields` option, treated as ignored fields.

::

  request: GET /users/1/?format=json&return_fields=username,skills&skip_fields=skills__id,skills__user
  status code: 200
  response: {
    "username": "foo",
    "skills": [
      {
        "name": "magic"
      },
      {
        "name": "magik"
      }
    ]
  }

how to use it?
----------------------------------------

using `django_returnfields.serializer_factory`

.. code-block:: python

  from rest_framework import viewsets
  from django_returnfields import serializer_factory

  class UserViewSet(viewsets.ModelViewSet):
      queryset = User.objects.all()
      serializer_class = serializer_factory(UserSerializer)


appendix
----------------------------------------

if you requesting with `aggressive` option, then, django_returnfields tries to use `Query.defer()` or `Query.only()`.
e.g.

::

  GET /users/1/?format=json&return_fields=username,skills&skip_fields=skills__id,skills__user&aggressive=1



example
----------------------------------------

.. code-block:: python

  ## models
  from django.db import models
  from django.contrib.auth.models import User


  class Skill(models.Model):
      name = models.CharField(max_length=255, default="", null=False)
      user = models.ForeignKey(User, null=False, related_name="skills")


  ## serializers
  from rest_framework import serializers

  class SkillSerializer(serializers.ModelSerializer):
      class Meta:
          model = Skill
          fields = ('id', 'user', 'name')


  class UserSerializer(serializers.ModelSerializer):
      skills = SkillSerializer(many=True, read_only=True)

      class Meta:
          model = User
          fields = ('id', 'url', 'username', 'email', 'is_staff', 'skills')

  ## viewsets
  from rest_framework import viewsets
  from django_returnfields import serializer_factory

  class UserViewSet(viewsets.ModelViewSet):
      queryset = User.objects.all()
      serializer_class = serializer_factory(UserSerializer)

  class SkillViewSet(viewsets.ModelViewSet):
      queryset = Skill.objects.all()
      serializer_class = serializer_factory(SkillSerializer)


  ## routes

  router = routers.DefaultRouter()
  router.register(r'users', viewsets.UserViewSet)
  router.register(r'skills', viewsets.SkillViewSet)

  urlpatterns = [
      url(r'^api/', include(router.urls)),
  ]
