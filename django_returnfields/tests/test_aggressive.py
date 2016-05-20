# -*- coding:utf-8 -*-
from django.test import TestCase
from .models import User


class ExtractCandidatesTests(TestCase):
    def _callFUT(self, model):
        from django_returnfields.aggressive import extract_candidates
        return extract_candidates(model)

    def test_for_prepare__load_candidates(self):
        from .models import Customer
        candidates = self._callFUT(Customer)
        expected = [
            'id',
            'name',
            'memo1',
            'memo2',
            'memo3',
        ]
        self.assertEqual(tuple(sorted(candidates.keys())), tuple(sorted(expected)))

    def test_for_prepare__load_candidates2(self):
        from .models import CustomerKarma
        candidates = self._callFUT(CustomerKarma)
        expected = [
            'customer',
            'point',
            'id',
        ]
        self.assertEqual(tuple(sorted(candidates.keys())), tuple(sorted(expected)))

    def test_for_prepare__load_candidates3(self):
        from .models import Order
        candidates = self._callFUT(Order)
        expected = [
            'customers',
            'id',
            'name',
            'price',
            'memo1',
            'memo2',
            'memo3',
        ]
        self.assertEqual(tuple(sorted(candidates.keys())), tuple(sorted(expected)))

    def test_for_prepare__load_candidates4(self):
        from .models import Item
        candidates = self._callFUT(Item)
        expected = [
            'order',
            'id',
            'name',
            'price',
            'memo1',
            'memo2',
            'memo3',
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


# class DeferQueryTests(TestCase):
#     def _callFUT(self, query, fields):
#         from django_returnfields.aggressive import safe_defer
#         return safe_defer(query, fields)

#     def test_safe_defer(self):
#         fields = ["xxxx", "username", "xxxx__id", "groups__name", "groups__name__xxxx", "xxx__yyy__zzz"]
#         qs = self._callFUT(User.objects.filter(groups__name=1), fields)
#         self.assertIn('SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined"', str(qs.query))

#     def test_safe_defer__many_to_one_rel__hasnot_attname(self):
#         fields = ["xxxx", "username", "xxxx__id", "skills__id", "skills__id__xxxx", "xxx__yyy__zzz"]
#         qs = self._callFUT(User.objects.filter(skills__name="foo"), fields)
#         self.assertIn('SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined"', str(qs.query))

#     def test_safe_defer__with_select_related(self):
#         from django.contrib.redirects.models import Redirect
#         fields = ["site"]
#         qs = Redirect.objects.select_related("site")
#         self.assertIn('JOIN', str(qs.query))
#         qs = self._callFUT(qs, fields)
#         self.assertNotIn('JOIN', str(qs.query))

#     def test_safe_defer__with_select_related__nested(self):
#         from django.contrib.redirects.models import Redirect
#         fields = ["site__name"]
#         qs = Redirect.objects.select_related("site")
#         self.assertIn('JOIN', str(qs.query))
#         qs = self._callFUT(qs, fields)
#         self.assertIn('JOIN', str(qs.query))


class OnlyQueryTests(TestCase):
    def _callFUT(self, query, fields):
        from django_returnfields.aggressive import safe_only
        return safe_only(query, fields)

    # def test_safe_only(self):
    #     fields = ["xxxx", "username", "xxxx__id", "groups__name", "groups__name__xxxx", "xxx__yyy__zzz"]
    #     qs = self._callFUT(User.objects.filter(groups__name=1), fields)
    #     self.assertIn('SELECT "auth_user"."id", "auth_user"."username" FROM', (str(qs.query)))

    # def test_safe_only__many_to_one_rel__does_not_have_attname(self):
    #     fields = ["xxxx", "username", "xxxx__id", "skills__id", "skills__id__xxxx", "xxx__yyy__zzz"]
    #     qs = self._callFUT(User.objects.filter(skills__id=1), fields)
    #     self.assertIn('SELECT "auth_user"."id", "auth_user"."username" FROM', (str(qs.query)))

    # def test_safe_only__with_select_related(self):
    #     from django.contrib.redirects.models import Redirect
    #     fields = ["id"]
    #     qs = Redirect.objects.select_related("site")
    #     self.assertIn('JOIN', str(qs.query))
    #     qs = self._callFUT(qs, fields)
    #     self.assertNotIn('JOIN', str(qs.query))

    # def test_safe_only__with_select_related__nested__keep(self):
    #     from django.contrib.redirects.models import Redirect
    #     fields = ["site__name"]
    #     qs = Redirect.objects.filter(site__name="foo").select_related("site")
    #     self.assertIn('JOIN', str(qs.query))
    #     qs = self._callFUT(qs, fields)
    #     self.assertIn('JOIN', str(qs.query))

    # def test_safe_only__with_prefetch_related(self):
    #     from django.contrib.sites.models import Site
        # Site.objects.prefetch_related()
        # fields = []
        # qs = Redirect.objects.filter(site__name="foo").select_related("site")
        # self.assertIn('JOIN', str(qs.query))
        # qs = self._callFUT(qs, fields)
        # self.assertIn('JOIN', str(qs.query))
