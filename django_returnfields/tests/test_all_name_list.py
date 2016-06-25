# -*- coding:utf-8 -*-
from django.test import TestCase
from . import serializers as s


class CollectAllNameListTests(TestCase):
    def _callFUT(self, serializer_class):
        from django_returnfields import collect_all_name_list
        return collect_all_name_list(serializer_class)

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
