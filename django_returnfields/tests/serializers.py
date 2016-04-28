# -*- coding:utf-8 -*-
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Group


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'is_staff')


class GroupSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Group
        fields = ('id', 'user', 'name')
