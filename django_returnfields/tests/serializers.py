# -*- coding:utf-8 -*-
from rest_framework import serializers
from .models import Skill, User, Group
from django_returnfields import depends


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


class GroupOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Group


class GroupUserSerializer(serializers.ModelSerializer):
    groups = GroupOnlySerializer(many=True)

    class Meta:
        model = User
        fields = ('id', 'groups', 'username')


class GroupSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Group
        fields = ('id', 'user', 'name')
