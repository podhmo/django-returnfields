# -*- coding:utf-8 -*-
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Skill


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'url', 'username', 'email', 'is_staff')


class SkillOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name')


class SkillUserSerializer(serializers.ModelSerializer):
    skills = SkillOnlySerializer(many=True)

    class Meta:
        model = User
        fields = ('id', 'skills', 'username')


class SkillSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Skill
        fields = ('id', 'user', 'name')
