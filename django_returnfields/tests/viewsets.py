# -*- coding:utf-8 -*-
from django.contrib.auth.models import User
from rest_framework import viewsets

from django_returnfields import return_fields_serializer_factory, Restriction

from . import serializers
from .models import Group


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = return_fields_serializer_factory(serializers.UserSerializer)


class UserViewSet2(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = return_fields_serializer_factory(
        serializers.UserSerializer,
        restriction=Restriction(include_key="include"))


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = return_fields_serializer_factory(serializers.GroupSerializer)
