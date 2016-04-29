# -*- coding:utf-8 -*-
from django.contrib.auth.models import User
from rest_framework import viewsets

from django_returnfields import serializer_factory, Restriction

from . import serializers
from .models import Skill


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializer_factory(serializers.UserSerializer)


class UserViewSet2(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializer_factory(
        serializers.UserSerializer,
        restriction=Restriction(include_key="include"))


class SkillUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializer_factory(serializers.SkillUserSerializer)


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = serializer_factory(serializers.SkillSerializer)
