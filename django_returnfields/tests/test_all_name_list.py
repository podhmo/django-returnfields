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


class CollectAllWithSourceOptionTests(TestCase):
    def _makeOne(self):
        from django_returnfields.optimize import NameListTranslator
        return NameListTranslator()

    def setUp(self):
        from .models import User, Skill

        class AnotherSkillSerializer(serializers.ModelSerializer):
            fullname = serializers.CharField(source="name")

            class Meta:
                model = Skill
                fields = ("id", "fullname")

        class AnotherUserSerializer(serializers.ModelSerializer):
            fullname = serializers.CharField(source="username")
            my_skills = AnotherSkillSerializer(many=True, source="skills")

            class Meta:
                model = User
                fields = ("id", "fullname", "my_skills")
        self.Serializer = AnotherUserSerializer

    def test_all_list(self):
        target = self._makeOne()
        actual = target.all_name_list(self.Serializer)
        expected = ['id', 'username', 'skills__id', 'skills__name']
        self.assertEqual(actual, expected)

    def test_translate(self):
        target = self._makeOne()
        name_list = ['my_skills__fullname', 'fullname']
        actual = target.translate(self.Serializer, name_list, {})
        expected = ["skills__name", "username"]
        self.assertEqual(actual, expected)


class CollectAllDeepNestedTests(TestCase):
    def _makeOne(self):
        from django_returnfields.optimize import NameListTranslator
        return NameListTranslator()

    def setUp(self):
        from django.contrib.auth.models import Permission, Group
        from .models import User, Skill
        # in django.contrib.auth.models
        #     permission *-* group, permission *-* user, permission *-* groups
        # in my tests.models:
        #     skill *- user

        class ContribPermissionSerializer(serializers.ModelSerializer):
            class Meta:
                model = Permission
                fields = "__all__"

        class SkillSerializer(serializers.ModelSerializer):
            class Meta:
                model = Skill
                fields = "__all__"

        class UserSerializer(serializers.ModelSerializer):
            skills = SkillSerializer(many=True)
            permissions = ContribPermissionSerializer(many=True)

            class Meta:
                model = User
                fields = "__all__"

        class ContribGroupSerializer(serializers.ModelSerializer):
            permissions = ContribPermissionSerializer(many=True)
            users = UserSerializer(many=True)

            class Meta:
                model = Group
                fields = "__all__"

        self.PermissionSerializer = ContribPermissionSerializer
        self.SkillSerializer = SkillSerializer
        self.UserSerializer = UserSerializer
        self.GroupSerializer = ContribGroupSerializer

    def test_with_deep_nested(self):
        target = self._makeOne()
        context = {}

        actual = target.translate(self.GroupSerializer, None, context)
        expected = [
            'id',
            'name',
            'permissions__id',
            'permissions__name',
            'permissions__codename',
            'permissions__content_type',
            'users__id',
            'users__last_login',
            'users__is_superuser',
            'users__username',
            'users__first_name',
            'users__last_name',
            'users__email',
            'users__is_staff',
            'users__is_active',
            'users__date_joined',
            'users__skills__id',
            'users__skills__name',
            'users__skills__user',
            'users__permissions__id',
            'users__permissions__name',
            'users__permissions__codename',
            'users__permissions__content_type',
            'users__password',
            'users__groups__id',
            'users__user_permissions__id',
        ]
        self.assertEqual(sorted(actual), sorted(expected))

    def test_with_deep_nested2(self):
        target = self._makeOne()
        context = {}

        actual = target.translate(self.GroupSerializer, ["users__permissions"], context)
        expected = [
            'users__permissions__codename',
            'users__permissions__content_type',
            'users__permissions__id',
            'users__permissions__name'
        ]
        self.assertEqual(sorted(actual), sorted(expected))


class CollectAllDependsTests(TestCase):
    def _getTarget(self):
        from django_returnfields import depends
        return depends

    def setUp(self):
        from .models import User
        depends = self._getTarget()

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
        self.Serializer = ForDependsTestUserSerializer

    def _makeTranslator(self):
        from django_returnfields.optimize import NameListTranslator
        return NameListTranslator()

    def test_with_depends_decorator__all(self):
        translator = self._makeTranslator()
        context = {}

        actual = translator.translate(self.Serializer, None, context)
        expected = ['id', 'username', 'username']
        self.assertEqual(actual, expected)

    def test_with_depends_decorator__not_matched(self):
        translator = self._makeTranslator()
        context = {}

        actual = translator.translate(self.Serializer, ["id"], context)
        expected = ['id']
        self.assertEqual(actual, expected)


class CollectAllContextualTests(TestCase):
    def _getTarget(self):
        from django_returnfields import contextual
        return contextual

    def _makeTranslator(self):
        from django_returnfields.optimize import NameListTranslator
        return NameListTranslator()

    def setUp(self):
        from .models import User

        contextual = self._getTarget()

        def has_xxx_context(xxx, replaced):
            def check(token, context):
                return replaced if xxx in context else []
            return check

        class ForContextualTestUserSerializer(serializers.ModelSerializer):
            class Meta:
                model = User
                fields = ('id', 'username')

            username = serializers.SerializerMethodField()

            @contextual(has_xxx_context('with_username', 'username'))
            def get_username(self, ob):
                return ob.username.split(" ", 1)[0]
        self.Serializer = ForContextualTestUserSerializer

    def test_with_contextual_decorator__deactivated(self):
        translator = self._makeTranslator()
        context = {}

        actual = translator.translate(self.Serializer, None, context)
        expected = ['id']
        self.assertEqual(actual, expected)

    def test_with_contextual_decorator__activated(self):
        translator = self._makeTranslator()
        context = {"with_username": True}

        actual = translator.translate(self.Serializer, None, context)
        expected = ['id', "username"]
        self.assertEqual(actual, expected)


class CollectAllContextualNestedTests(TestCase):
    def _getTarget(self):
        from django_returnfields import contextual
        return contextual

    def _makeTranslator(self):
        from django_returnfields.optimize import NameListTranslator
        return NameListTranslator()

    def setUp(self):
        from .models import User
        from .serializers import SkillSerializer

        contextual = self._getTarget()

        def has_nested(serializer_class, key_name, default):
            def _has_nested(token, context):
                if context.get(key_name, False):
                    name_list = token.translator.translate(serializer_class, None, context)
                    return ["{}__{}".format(token.queryname, name) for name in name_list]
                else:
                    return default
            return _has_nested

        class ForContextualTestUserSerializer(serializers.ModelSerializer):
            skills = serializers.SerializerMethodField()

            class Meta:
                model = User
                fields = ('id', 'username', 'skills')

            @contextual(has_nested(SkillSerializer, 'with_skills', default=[]))
            def get_skills(self, ob):
                if self.context.get("with_skills", False):
                    return SkillSerializer(ob.skills, many=True).data
                else:
                    return []

        self.Serializer = ForContextualTestUserSerializer

    def test_with_contextual_decorator__deactivated(self):
        translator = self._makeTranslator()
        context = {}

        actual = translator.translate(self.Serializer, None, context)
        expected = ['id', 'username']
        self.assertEqual(actual, expected)

    def test_with_contextual_decorator__activated(self):
        translator = self._makeTranslator()
        context = {"with_skills": True}

        actual = translator.translate(self.Serializer, None, context)
        expected = ['id', 'username', 'skills__id', 'skills__user__id', 'skills__user__url', 'skills__user__username', 'skills__user__email', 'skills__user__is_staff', 'skills__name']
        self.assertEqual(actual, expected)
