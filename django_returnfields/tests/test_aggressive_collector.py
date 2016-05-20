# -*- coding:utf-8 -*-
from django.test import TestCase
from django.contrib.auth.models import User


class ExtractCandidatesTests(TestCase):
    def _callFUT(self, model):
        from django_returnfields.aggressive import extract_candidates
        return extract_candidates(model)

    def test_for_prepare__load_candidates(self):
        candidates = self._callFUT(User)
        expected = [
            'date_joined',
            'email',
            'first_name',
            'groups',
            'id',
            'is_active',
            'is_staff',
            'is_superuser',
            'last_login',
            'last_name',
            'password',
            'user_permissions',
            'username'
        ]
        self.assertEqual(tuple(sorted(candidates.keys())), tuple(sorted(expected)))


class CollectorTests(TestCase):
    def _makeOne(self):
        from django_returnfields.aggressive import CorrectNameCollector
        return CorrectNameCollector()

    def test_it__flatten(self):
        target = self._makeOne()
        result = tuple(sorted(target.collect(User, ["id", "is_active"])))
        expected = tuple(sorted(["id", "is_active"]))
        self.assertEqual(result, expected)

    def test_it__flaten__with_noisy_names(self):
        target = self._makeOne()
        result = tuple(sorted(target.collect(User, ["id", "is_active", "xxxxx"])))
        expected = tuple(sorted(["id", "is_active"]))
        self.assertEqual(result, expected)

    def test_it__nested(self):
        target = self._makeOne()
        result = tuple(sorted(target.collect(User, ["id", "groups__id"])))
        expected = tuple(sorted(["id", "groups__id"]))
        self.assertEqual(result, expected)

    def test_it__nested__with_noisy_relation(self):
        target = self._makeOne()
        result = tuple(sorted(target.collect(User, ["id", "groups__id", "xxxxx__id"])))
        expected = tuple(sorted(["id", "groups__id"]))
        self.assertEqual(result, expected)

    def test_it__nested__with_noisy_name(self):
        target = self._makeOne()
        result = tuple(sorted(target.collect(User, ["id", "groups__id", "groups__xxxxx"])))
        expected = tuple(sorted(["id", "groups__id"]))
        self.assertEqual(result, expected)


class DeferQueryTests(TestCase):
    def _callFUT(self, query, fields):
        from django_returnfields.aggressive import safe_defer
        return safe_defer(query, fields)

    def test_safe_defer(self):
        fields = ["xxxx", "username", "xxxx__id", "groups__name", "groups__name__xxxx", "xxx__yyy__zzz"]
        qs = self._callFUT(User.objects.filter(groups__name=1), fields)
        self.assertIn('SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined"', str(qs.query))

    def test_safe_defer__many_to_one_rel__hasnot_attname(self):
        fields = ["xxxx", "username", "xxxx__id", "skills__id", "skills__id__xxxx", "xxx__yyy__zzz"]
        qs = self._callFUT(User.objects.filter(skills__name="foo"), fields)
        self.assertIn('SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined"', str(qs.query))


class OnlyQueryTests(TestCase):
    def _callFUT(self, query, fields):
        from django_returnfields.aggressive import safe_only
        return safe_only(query, fields)

    def test_safe_only(self):
        fields = ["xxxx", "username", "xxxx__id", "groups__name", "groups__name__xxxx", "xxx__yyy__zzz"]
        qs = self._callFUT(User.objects.filter(groups__name=1), fields)
        self.assertIn('SELECT "auth_user"."id", "auth_user"."username"', (str(qs.query)))

    def test_safe_only__many_to_one_rel__does_not_have_attname(self):
        fields = ["xxxx", "username", "xxxx__id", "skills__id", "skills__id__xxxx", "xxx__yyy__zzz"]
        qs = self._callFUT(User.objects.filter(skills__id=1), fields)
        self.assertIn('SELECT "auth_user"."id", "auth_user"."username"', (str(qs.query)))

    def test_safe_only__with_select_related(self):
        from django.contrib.auth.models import Permission
        fields = ["id"]
        qs = Permission.objects.select_related("content_type")
        qs = self._callFUT(qs, fields)
        print(qs.query)
