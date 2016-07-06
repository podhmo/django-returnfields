# -*- coding:utf-8 -*-
from django.test import TestCase
from rest_framework import serializers
from . import serializers as s


class CollectAllNameListTests(TestCase):
    def _callFUT(self, serializer_class):
        from django_returnfields.optimize import NameListTranslator
        return NameListTranslator().all_name_list(serializer_class)

    def test_group_only(self):
        actual = self._callFUT(s.GroupOnlySerializer)
        expected = ["id", "name", "permissions__id"]
        self.assertEqual(actual, expected)

    def test_skill_only(self):
        actual = self._callFUT(s.SkillOnlySerializer)
        expected = ["id", "name"]
        self.assertEqual(actual, expected)

    def test_user(self):
        actual = self._callFUT(s.UserSerializer)
        expected = ['id', 'url', 'username', 'email', 'is_staff']
        self.assertEqual(actual, expected)

    def test_skill_user(self):
        actual = self._callFUT(s.SkillUserSerializer)
        expected = ['id', 'skills__id', 'skills__name', 'username']
        self.assertEqual(actual, expected)

    def test_skill(self):
        actual = self._callFUT(s.SkillSerializer)
        expected = ['id', 'user__id', 'user__url', 'user__username', 'user__email', 'user__is_staff', 'name']
        self.assertEqual(actual, expected)

    def test_group_user(self):
        actual = self._callFUT(s.GroupUserSerializer)
        expected = ['id', 'groups__id', 'groups__name', 'groups__permissions__id', 'username']
        self.assertEqual(actual, expected)

    def test_group(self):
        actual = self._callFUT(s.GroupSerializer)
        expected = ['id', 'user__id', 'user__url', 'user__username', 'user__email', 'user__is_staff', 'name']
        self.assertEqual(actual, expected)

    def test_fields_value_is___all__(self):
        from .models import User

        class SlugUserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = '__all__'

        actual = self._callFUT(SlugUserSerializer)
        expected = ['id', 'password', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined', 'groups__id', 'user_permissions__id']
        self.assertEqual(actual, expected)

    def test_with_depends_decorator(self):
        from .models import User
        from django_returnfields import depends

        class ForDependsTestUserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ('id', 'first_name', "last_name")

            first_name = serializers.SerializerMethodField()
            last_name = serializers.SerializerMethodField()

            @depends("username")
            def get_first_name(self, ob):
                return ob.username.split(" ", 1)[0]

            @depends("username")
            def get_last_name(self, ob):
                return ob.username.split(" ", 1)[1]

        actual = self._callFUT(ForDependsTestUserSerializer)
        expected = ['id', 'username', 'username']
        self.assertEqual(actual, expected)
