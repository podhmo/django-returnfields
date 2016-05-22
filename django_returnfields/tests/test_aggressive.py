# -*- coding:utf-8 -*-
from django.test import TestCase
from . import models as m


class ExtractCandidatesTests(TestCase):
    def _callFUT(self, model):
        from django_returnfields.aggressive import extract_candidates
        return extract_candidates(model)

    def test_for_prepare__load_candidates(self):
        candidates = self._callFUT(m.Customer)
        expected = [
            'id',
            'name',
            'memo1',
            'memo2',
            'memo3',
            'orders',
            'karma',
        ]
        self.assertEqual(tuple(sorted(candidates.keys())), tuple(sorted(expected)))

    def test_for_prepare__load_candidates2(self):
        candidates = self._callFUT(m.CustomerKarma)
        expected = [
            'id',
            'point',
            'customer',
            'memo1',
            'memo2',
            'memo3',
        ]
        self.assertEqual(tuple(sorted(candidates.keys())), tuple(sorted(expected)))

    def test_for_prepare__load_candidates3(self):
        from .models import Order
        candidates = self._callFUT(Order)
        expected = [
            'id',
            'name',
            'price',
            'memo1',
            'memo2',
            'memo3',
            'items',
            'customers',
        ]
        self.assertEqual(tuple(sorted(candidates.keys())), tuple(sorted(expected)))

    def test_for_prepare__load_candidates4(self):
        candidates = self._callFUT(m.Item)
        expected = [
            'id',
            'name',
            'price',
            'memo1',
            'memo2',
            'memo3',
            'order',
        ]
        self.assertEqual(tuple(sorted(candidates.keys())), tuple(sorted(expected)))


class CollectorTests(TestCase):
    def _makeOne(self):
        from django_returnfields.aggressive import HintExtractor
        return HintExtractor()

    def _callFUT(self, extractor, name_list):
        return extractor.extract(m.Item, name_list)

    def test_it__flatten(self):
        target = self._makeOne()
        pair = self._callFUT(target, ["id", "name"])
        result = tuple(sorted(pair.for_select))
        expected = tuple(sorted(["id", "name"]))
        self.assertEqual(result, expected)

        result = tuple(sorted(pair.for_join))
        expected = tuple(sorted([]))
        self.assertEqual(result, expected)

    def test_it__flaten__with_noisy_names(self):
        target = self._makeOne()
        pair = self._callFUT(target, ["id", "name", "xxxxx"])
        result = tuple(sorted(pair.for_select))
        expected = tuple(sorted(["id", "name"]))
        self.assertEqual(result, expected)

        result = tuple(sorted(pair.for_join))
        expected = tuple(sorted([]))
        self.assertEqual(result, expected)

    def test_it__nested(self):
        target = self._makeOne()
        pair = self._callFUT(target, ["id", "order__id"])
        result = tuple(sorted(pair.for_select))
        expected = tuple(sorted(["id", "order__id"]))
        self.assertEqual(result, expected)

        result = tuple(sorted(pair.for_join))
        expected = tuple(sorted([]))
        self.assertEqual(result, expected)

    def test_it__nested__with_noisy_relation(self):
        target = self._makeOne()
        pair = self._callFUT(target, ["id", "order__id", "xxxxx__id"])
        result = tuple(sorted(pair.for_select))
        expected = tuple(sorted(["id", "order__id"]))
        self.assertEqual(result, expected)

        result = tuple(sorted(pair.for_join))
        expected = tuple(sorted([]))
        self.assertEqual(result, expected)

    def test_it__nested__with_noisy_name(self):
        target = self._makeOne()
        pair = self._callFUT(target, ["id", "order__id", "order__xxxxx"])
        result = tuple(sorted(pair.for_select))
        expected = tuple(sorted(["id", "order__id"]))
        self.assertEqual(result, expected)

        result = tuple(sorted(pair.for_join))
        expected = tuple(sorted([]))
        self.assertEqual(result, expected)


class DeferQueryTests(TestCase):
    def _callFUT(self, query, fields):
        from django_returnfields.aggressive import safe_defer
        return safe_defer(query, fields)

    def test_safe_defer__one_to_one(self):
        fields = ["xxxx", "name", "memo1"]
        qs = m.Customer.objects.all()
        self.assertNotIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertNotIn("JOIN", str(optimized.query))
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo1", str(optimized.query))

    def test_safe_defer__one_to_one__with_join_by_filter(self):
        fields = ["xxxx", "name", "memo1"]
        qs = m.Customer.objects.filter(karma__point=0)

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))

        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo1", str(optimized.query))

    def test_safe_defer__one_to_one__with_join(self):
        fields = ["xxxx", "name", "memo1", "karma__memo1"]
        qs = m.Customer.objects.select_related("karma")

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))

        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo1", str(optimized.query))

    def test_safe_defer__one_to_one__with_join__rel(self):
        fields = ["xxxx", "point", "memo1", "customer__memo1"]
        qs = m.CustomerKarma.objects.select_related("customer")

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo1", str(optimized.query))

    def test_safe_only__many_to_many__with_prefetch(self):
        fields = ["xxxx", "name", "memo1", "customers__name", "customers__memo1", "customers__yyyy"]
        qs = m.Order.objects.all().prefetch_related("customers")

        self.assertNotIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertNotIn("JOIN", str(optimized.query))

        self.assertEqual(optimized._prefetch_related_lookups, ["customers"])
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo1", str(optimized.query))

    def test_safe_only__many_to_many__not_without_prefetch(self):
        fields = ["xxxx", "name", "memo1"]
        qs = m.Order.objects.all().prefetch_related("customers")

        self.assertNotIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertNotIn("JOIN", str(optimized.query))

        self.assertEqual(optimized._prefetch_related_lookups, ["customers"])
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo1", str(optimized.query))

    def test_safe_only__many_to_many__with_join__by_filter(self):
        fields = ["xxxx", "name", "memo1", "customers__memo1"]
        qs = m.Order.objects.all().prefetch_related("customers").filter(customers__name="foo")

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo1", str(optimized.query))


class OnlyQueryTests(TestCase):
    def _callFUT(self, query, fields):
        from django_returnfields.aggressive import safe_only
        return safe_only(query, fields)

    def _getPrefetchLookups(self, qs):
        from django.db.models.query import normalize_prefetch_lookups
        return normalize_prefetch_lookups(qs._prefetch_related_lookups)

    def test_safe_only__one_to_one(self):
        fields = ["xxxx", "name", "memo1"]
        qs = m.Customer.objects.all()
        self.assertNotIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertNotIn("JOIN", str(optimized.query))
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__one_to_one__with_join_by_filter(self):
        fields = ["xxxx", "name", "memo1"]
        qs = m.Customer.objects.filter(karma__point=0)

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))

        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__one_to_one__without_join(self):
        fields = ["xxxx", "name", "memo1"]
        qs = m.Customer.objects.select_related("karma")

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertNotIn("JOIN", str(optimized.query))

        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__one_to_one__with_join__rel(self):
        fields = ["xxxx", "point", "memo1", "customer__memo2"]
        qs = m.CustomerKarma.objects.select_related("customer")

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__one_to_one__with_join(self):
        fields = ["xxxx", "name", "memo1", "karma__memo2"]
        qs = m.Customer.objects.select_related("karma")

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        # bug
        # self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__one_to_many(self):
        fields = ["xxxx", "name", "memo1", "items__name", "items__memo2", "items__yyyy"]
        qs = m.Order.objects.all().prefetch_related("items")
        self.assertNotIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertNotIn("JOIN", str(optimized.query))

        self.assertEqual(optimized._prefetch_related_lookups, ["items"])
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__one_to_many__with_join(self):
        fields = ["xxxx", "name", "memo1", "items__name", "items__memo2", "items__yyyy"]
        qs = m.Order.objects.all().filter(items__name="foo").prefetch_related("items")

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))

        self.assertEqual(optimized._prefetch_related_lookups, ["items"])
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__one_to_many__without_prefetch(self):
        fields = ["xxxx", "name", "memo1"]
        qs = m.Order.objects.all().prefetch_related("items")

        self.assertNotIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertNotIn("JOIN", str(optimized.query))

        self.assertEqual(qs._prefetch_related_lookups, ["items"])
        self.assertEqual(optimized._prefetch_related_lookups, [])
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__many_to_one__with_join(self):
        fields = ["xxxx", "name", "memo1", "order__name", "order__memo2", "order__yyyy"]
        qs = m.Item.objects.all().select_related("order")

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))

        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__many_to_one__without_join(self):
        fields = ["xxxx", "name", "memo1"]
        qs = m.Item.objects.all().select_related("order")

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertNotIn("JOIN", str(optimized.query))
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__many_to_one__with_join__by_filter(self):
        fields = ["xxxx", "name", "memo1"]
        qs = m.Item.objects.all().filter(order__name="foo")

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__many_to_many__with_prefetch(self):
        fields = ["xxxx", "name", "memo1", "customers__name", "customers__memo2", "customers__yyyy"]
        qs = m.Order.objects.all().prefetch_related("customers")

        self.assertNotIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertNotIn("JOIN", str(optimized.query))

        self.assertEqual(optimized._prefetch_related_lookups, ["customers"])
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__many_to_many__without_prefetch(self):
        fields = ["xxxx", "name", "memo1"]
        qs = m.Order.objects.all().prefetch_related("customers")

        self.assertNotIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertNotIn("JOIN", str(optimized.query))

        self.assertEqual(optimized._prefetch_related_lookups, [])
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    def test_safe_only__many_to_many__with_join__by_filter(self):
        fields = ["xxxx", "name", "memo1", "customers__memo2"]
        qs = m.Order.objects.all().prefetch_related("customers").filter(customers__name="foo")

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))
