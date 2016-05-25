# -*- coding:utf-8 -*-
from django.test import TestCase
from . import models as m


class ExtractHintDictTests(TestCase):
    def _callFUT(self, model):
        from django_returnfields.aggressive import HintMap
        return HintMap().extract(model)

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


class ExtractorClassifyTests(TestCase):
    def _makeOne(self):
        from django_returnfields.aggressive import HintExtractor
        return HintExtractor()

    def _makeInspector(self):
        from django_returnfields.aggressive import Inspector
        return Inspector()

    # relation: CustomerKarma - Customer *-* Order -* Item, Customer -* CustomerPosition
    def test_it_nest1__star(self):
        model = m.CustomerKarma
        query = ["*"]
        actual = self._makeOne().extract(model, query)
        expected = "Result(fields=[Hint(name='id'), Hint(name='memo1'), Hint(name='memo2'), Hint(name='memo3'), Hint(name='point')])"
        self.assertEqual(str(actual), expected)

    def test_it_nest2__star_id__karma(self):
        model = m.CustomerKarma
        query = ["*__id"]
        actual = self._makeOne().extract(model, query)
        expected = "Result(reverse_related=[Hint(name='customer')], foreign_keys=['customer_id'], subresults=[Result(name='customer', fields=[Hint(name='id')])])"
        self.assertEqual(str(actual), expected)

    def test_it_nest2__star_id__customer(self):
        model = m.Customer
        query = ["*__id"]
        actual = self._makeOne().extract(model, query)
        expected = "Result(related=[Hint(name='customerposition'), Hint(name='karma'), Hint(name='orders')], subresults=[Result(name='customerposition', fields=[Hint(name='id')]), Result(name='karma', fields=[Hint(name='id')]), Result(name='orders', fields=[Hint(name='id')])])"
        self.assertEqual(str(actual), expected)

    def test_it_nest2__star_id__order(self):
        model = m.Order
        query = ["*__id"]
        actual = self._makeOne().extract(model, query)
        expected = "Result(related=[Hint(name='items')], reverse_related=[Hint(name='customers')], subresults=[Result(name='customers', fields=[Hint(name='id')]), Result(name='items', fields=[Hint(name='id')])])"
        self.assertEqual(str(actual), expected)

    def test_it_nest2__star_id__item(self):
        model = m.Item
        query = ["*__id"]
        actual = self._makeOne().extract(model, query)
        expected = "Result(reverse_related=[Hint(name='order')], foreign_keys=['order_id'], subresults=[Result(name='order', fields=[Hint(name='id')])])"
        self.assertEqual(str(actual), expected)

    def test_it_nest2__star_id__customerposition(self):
        model = m.CustomerPosition
        query = ["*__id"]
        actual = self._makeOne().extract(model, query)
        expected = "Result(reverse_related=[Hint(name='customer')], foreign_keys=['customer_id'], subresults=[Result(name='customer', fields=[Hint(name='id')])])"
        self.assertEqual(str(actual), expected)

    def test_it_nest__each_field__customer(self):
        model = m.Customer
        query = ["karma__memo1", "orders__memo2", "customerposition__memo3"]
        actual = self._makeOne().extract(model, query)
        expected = "Result(related=[Hint(name='customerposition'), Hint(name='karma'), Hint(name='orders')], subresults=[Result(name='customerposition', fields=[Hint(name='memo3')]), Result(name='karma', fields=[Hint(name='memo1')]), Result(name='orders', fields=[Hint(name='memo2')])])"
        self.assertEqual(str(actual), expected)

    def test_it_nest3__star_id__item(self):
        model = m.Item
        query = ["*__*__id"]
        actual = self._makeOne().extract(model, query)
        expected = "Result(reverse_related=[Hint(name='order')], foreign_keys=['order_id'], subresults=[Result(name='order', reverse_related=[Hint(name='customers')], subresults=[Result(name='customers', fields=[Hint(name='id')])])])"
        self.assertEqual(str(actual), expected)

    def test_it_nest3__star_id__item__select__skiped_attributes__directly(self):
        model = m.Item
        query = ["*__*__id", "order__items"]
        actual = self._makeOne().extract(model, query)
        expected = "Result(reverse_related=[Hint(name='order'), Hint(name='order')], foreign_keys=['order_id', 'order_id'], subresults=[Result(name='order', related=[Hint(name='items')], reverse_related=[Hint(name='customers')], subresults=[Result(name='customers', fields=[Hint(name='id')])])])"
        self.assertEqual(str(actual), expected)

    def test_it_nest6__id__item(self):
        model = m.Item
        query = ["id", "*__id", "*__*__id", "*__*__*__id", "*__*__*__*__id", "*__*__*__*__*__id"]
        actual = self._makeOne().extract(model, query)

        inspector = self._makeInspector()
        self.assertEqual(inspector.depth(actual), 4)
        # Item -> {order: {customers: {customerposition: {}, karma: {}}}}
        expected = "Result(fields=[Hint(name='id')], reverse_related=[Hint(name='order')], foreign_keys=['order_id'], subresults=[Result(name='order', fields=[Hint(name='id')], reverse_related=[Hint(name='customers')], subresults=[Result(name='customers', fields=[Hint(name='id')], related=[Hint(name='customerposition'), Hint(name='karma')], subresults=[Result(name='customerposition', fields=[Hint(name='id')]), Result(name='karma', fields=[Hint(name='id')])])])])"
        self.assertEqual(str(actual), expected)

    def test_it_nest6__id__customer(self):
        model = m.Customer
        query = ["id", "*__id", "*__*__id", "*__*__*__id", "*__*__*__*__id", "*__*__*__*__*__id"]
        actual = self._makeOne().extract(model, query)

        inspector = self._makeInspector()
        self.assertEqual(inspector.depth(actual), 3)
        # Customer -> {customerposition: {}, karma: {}, orders: {items: {}}}
        expected = "Result(fields=[Hint(name='id')], related=[Hint(name='customerposition'), Hint(name='karma'), Hint(name='orders')], subresults=[Result(name='customerposition', fields=[Hint(name='id')]), Result(name='karma', fields=[Hint(name='id')]), Result(name='orders', fields=[Hint(name='id')], related=[Hint(name='items')], subresults=[Result(name='items', fields=[Hint(name='id')])])])"
        self.assertEqual(str(actual), expected)


class OnlyQueryTests(TestCase):
    def _callFUT(self, query, fields):
        from django_returnfields.aggressive import safe_only
        return safe_only(query, fields)

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

    def test_safe_only__one_to_one__with_join__rel__star(self):
        fields = ["*", "customer__*"]
        qs = m.CustomerKarma.objects.select_related("customer")

        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))
        self.assertEqual(len(str(optimized.query)), len(str(qs.query)))
        self.assertIn("memo3", str(optimized.query))

    def test_safe_only__one_to_one__with_join(self):
        fields = ["xxxx", "name", "memo1", "karma__memo2"]
        qs = m.Customer.objects.select_related("karma")
        self.assertIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))
        self.assertLess(len(str(optimized.query)), len(str(qs.query)))

        # django's limitation
        # self.assertNotIn("memo3", str(optimized.query))

    def test_it(self):
        fields = ["xxxx", "name", "memo1", "customer__name", "substitute__name"]
        qs = m.CustomerPosition.objects.all()
        self.assertNotIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))
        # self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    # def test_safe_only__one_to_many(self):
    #     fields = ["xxxx", "name", "memo1", "items__name", "items__memo2", "items__yyyy"]
    #     qs = m.Order.objects.all().prefetch_related("items")
    #     self.assertNotIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertNotIn("JOIN", str(optimized.query))

    #     self.assertEqual(optimized._prefetch_related_lookups, ["items"])
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test_safe_only__one_to_many__with_join(self):
    #     fields = ["xxxx", "name", "memo1", "items__name", "items__memo2", "items__yyyy"]
    #     qs = m.Order.objects.all().filter(items__name="foo").prefetch_related("items")

    #     self.assertIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertIn("JOIN", str(optimized.query))

    #     self.assertEqual(optimized._prefetch_related_lookups, ["items"])
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test_safe_only__one_to_many__without_prefetch(self):
    #     fields = ["xxxx", "name", "memo1"]
    #     qs = m.Order.objects.all().prefetch_related("items")

    #     self.assertNotIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertNotIn("JOIN", str(optimized.query))

    #     self.assertEqual(qs._prefetch_related_lookups, ["items"])
    #     self.assertEqual(optimized._prefetch_related_lookups, [])
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test_safe_only__many_to_one__with_join(self):
    #     fields = ["xxxx", "name", "memo1", "order__name", "order__memo2", "order__yyyy"]
    #     qs = m.Item.objects.all().select_related("order")

    #     self.assertIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertIn("JOIN", str(optimized.query))

    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test_safe_only__many_to_one__without_join(self):
    #     fields = ["xxxx", "name", "memo1"]
    #     qs = m.Item.objects.all().select_related("order")

    #     self.assertIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertNotIn("JOIN", str(optimized.query))
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test_safe_only__many_to_one__with_join__by_filter(self):
    #     fields = ["xxxx", "name", "memo1"]
    #     qs = m.Item.objects.all().filter(order__name="foo")

    #     self.assertIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertIn("JOIN", str(optimized.query))
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test_safe_only__many_to_many__with_prefetch(self):
    #     fields = ["xxxx", "name", "memo1", "customers__name", "customers__memo2", "customers__yyyy"]
    #     qs = m.Order.objects.all().prefetch_related("customers")

    #     self.assertNotIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertNotIn("JOIN", str(optimized.query))

    #     self.assertEqual(optimized._prefetch_related_lookups, ["customers"])
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test_safe_only__many_to_many__without_prefetch(self):
    #     fields = ["xxxx", "name", "memo1"]
    #     qs = m.Order.objects.all().prefetch_related("customers")

    #     self.assertNotIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertNotIn("JOIN", str(optimized.query))

    #     self.assertEqual(optimized._prefetch_related_lookups, [])
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test_safe_only__many_to_many__with_join__by_filter(self):
    #     fields = ["xxxx", "name", "memo1", "customers__memo2"]
    #     qs = m.Order.objects.all().prefetch_related("customers").filter(customers__name="foo")

    #     self.assertIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertIn("JOIN", str(optimized.query))
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))
