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
            'customerposition',
            'customerposition_set',
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
        expected = "Result(reverse_related=[Hint(name='customer'), Hint(name='substitute')], foreign_keys=['customer_id', 'substitute_id'], subresults=[Result(name='customer', fields=[Hint(name='id')]), Result(name='substitute', fields=[Hint(name='id')])])"
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
        self.assertEqual(inspector.depth(actual), 6)
        expected = "Result(fields=[Hint(name='id')], reverse_related=[Hint(name='order')], foreign_keys=['order_id'], subresults=[Result(name='order', fields=[Hint(name='id')], reverse_related=[Hint(name='customers')], subresults=[Result(name='customers', fields=[Hint(name='id')], related=[Hint(name='customerposition'), Hint(name='karma')], subresults=[Result(name='customerposition', fields=[Hint(name='id')], reverse_related=[Hint(name='customer'), Hint(name='substitute')], foreign_keys=['customer_id', 'substitute_id'], subresults=[Result(name='customer', fields=[Hint(name='id')], related=[Hint(name='customerposition'), Hint(name='karma')], subresults=[Result(name='customerposition', fields=[Hint(name='id')]), Result(name='karma', fields=[Hint(name='id')])]), Result(name='substitute', fields=[Hint(name='id')], related=[Hint(name='karma')], subresults=[Result(name='karma', fields=[Hint(name='id')])])]), Result(name='karma', fields=[Hint(name='id')])])])])"
        self.assertEqual(str(actual), expected)

    def test_it_nest6__id__customer(self):
        model = m.Customer
        query = ["id", "*__id", "*__*__id", "*__*__*__id", "*__*__*__*__id", "*__*__*__*__*__id"]
        actual = self._makeOne().extract(model, query)

        inspector = self._makeInspector()
        self.assertEqual(inspector.depth(actual), 6)
        expected = "Result(fields=[Hint(name='id')], related=[Hint(name='customerposition'), Hint(name='karma'), Hint(name='orders')], subresults=[Result(name='customerposition', fields=[Hint(name='id')]), Result(name='karma', fields=[Hint(name='id')]), Result(name='orders', fields=[Hint(name='id')], related=[Hint(name='items')], subresults=[Result(name='items', fields=[Hint(name='id')], reverse_related=[Hint(name='order')], foreign_keys=['order_id'], subresults=[Result(name='order', fields=[Hint(name='id')], reverse_related=[Hint(name='customers')], subresults=[Result(name='customers', fields=[Hint(name='id')], related=[Hint(name='customerposition'), Hint(name='karma')], subresults=[Result(name='customerposition', fields=[Hint(name='id')]), Result(name='karma', fields=[Hint(name='id')])])])])])])"
        self.assertEqual(str(actual), expected)

    def test_it_usualy_case(self):
        model = m.CustomerKarma
        query = ["id", "customer__id", "customer__customerposition__id"]
        actual = self._makeOne().extract(model, query)

        inspector = self._makeInspector()
        self.assertEqual(inspector.depth(actual), 3)
        expected = "Result(fields=[Hint(name='id')], reverse_related=[Hint(name='customer')], foreign_keys=['customer_id'], subresults=[Result(name='customer', fields=[Hint(name='id')], related=[Hint(name='customerposition')], subresults=[Result(name='customerposition', fields=[Hint(name='id')])])])"
        self.assertEqual(str(actual), expected)


class OnlyQueryTests(TestCase):
    def _callFUT(self, query, fields):
        from django_returnfields.aggressive import safe_only
        return safe_only(query, fields)

    def _makeCustomerStructure(self, structure):
        for customer_structure in structure:
            customer = m.Customer.objects.create(name=customer_structure["name"])
            if "karma" in customer_structure:
                m.CustomerKarma.objects.create(customer=customer, point=customer_structure["karma"]["point"])

    def test__one_to_one__dejoin(self):
        # setup
        structure = [
            {"name": "foo", "karma": {"point": 10}},
            {"name": "bar", "karma": {"point": 1}}
        ]
        self._makeCustomerStructure(structure)
        for msg, before_count, after_count, has_join, qs_filter in [
                ("with select related", 1, 1, True, lambda qs: qs.all().select_related("karma")),
                ("without select related", 1, 1, False, lambda qs: qs.all()),
        ]:
            with self.subTest(msg=msg, before_count=before_count, after_count=after_count, has_join=has_join, qs_filter=qs_filter):
                qs = qs_filter(m.Customer.objects)
                fields = ["xxxx", "name", "memo1"]
                optimized = self._callFUT(qs, fields)

                self.assertEqual("JOIN" in str(qs.query), has_join)
                with self.assertNumQueries(before_count):
                    customers = [(c.id, c.name) for c in qs]
                    self.assertEqual(len(customers), 2)
                    self.assertIn("memo3", str(qs.query))

                self.assertNotIn("JOIN", str(optimized.query))
                with self.assertNumQueries(after_count):
                    customers = [(c.id, c.name) for c in optimized]
                    self.assertEqual(len(customers), 2)
                    self.assertNotIn("memo3", str(optimized.query))

    def test__one_to_one__join_by_filter(self):
        # setup
        structure = [
            {"name": "foo", "karma": {"point": 10}},
            {"name": "bar", "karma": {"point": 1}}
        ]
        self._makeCustomerStructure(structure)
        for msg, before_count, after_count, has_join, qs_filter in [
                ("with select related", 1, 1, True, lambda qs: qs.all().filter(karma__point=10).select_related("karma")),
                ("without select related", 1, 1, False, lambda qs: qs.all().filter(karma__point=10)),
        ]:
            with self.subTest(msg=msg, before_count=before_count, after_count=after_count, has_join=has_join, qs_filter=qs_filter):
                qs = qs_filter(m.Customer.objects)
                fields = ["xxxx", "name", "memo1"]
                optimized = self._callFUT(qs, fields)

                self.assertIn("JOIN", str(optimized.query))
                with self.assertNumQueries(before_count):
                    customers = [(c.id, c.name) for c in qs]
                    self.assertEqual(len(customers), 1)
                    self.assertIn("memo3", str(qs.query))

                self.assertIn("JOIN", str(optimized.query))
                with self.assertNumQueries(after_count):
                    customers = [(c.id, c.name) for c in optimized]
                    self.assertEqual(len(customers), 1)
                    self.assertNotIn("memo3", str(optimized.query))

    def test__one_to_one__join_by_selection(self):
        # setup
        structure = [
            {"name": "foo", "karma": {"point": 10}},
            {"name": "bar", "karma": {"point": 1}}
        ]
        self._makeCustomerStructure(structure)
        for msg, before_count, after_count, has_join, qs_filter in [
                ("with select related", 1, 1, True, lambda qs: qs.all().select_related("karma")),
                ("without select related", 1, 1, False, lambda qs: qs.all()),
        ]:
            with self.subTest(msg=msg, before_count=before_count, after_count=after_count, has_join=has_join, qs_filter=qs_filter):
                qs = qs_filter(m.Customer.objects)
                fields = ["xxxx", "name", "memo1", "karma__point"]
                optimized = self._callFUT(qs, fields)

                self.assertEqual("JOIN" in str(qs.query), has_join)
                with self.assertNumQueries(before_count):
                    customers = [(c.id, c.name) for c in qs]
                    self.assertEqual(len(customers), 2)
                    self.assertIn("memo3", str(qs.query))

                self.assertIn("JOIN", str(optimized.query))
                with self.assertNumQueries(after_count):
                    customers = [(c.id, c.name) for c in optimized]
                    self.assertEqual(len(customers), 2)

                    # django's limitation
                    self.assertIn("memo3", str(optimized.query))

    def test__one_to_onerel__join_by_selection(self):
        # setup
        structure = [
            {"name": "foo", "karma": {"point": 10}},
            {"name": "bar", "karma": {"point": 1}}
        ]
        self._makeCustomerStructure(structure)
        for msg, before_count, after_count, has_join, qs_filter in [
                ("with select related", 1, 1, True, lambda qs: qs.all().select_related("customer")),
                ("without select related", 3, 1, False, lambda qs: qs.all()),
        ]:
            with self.subTest(msg=msg, before_count=before_count, after_count=after_count, has_join=has_join, qs_filter=qs_filter):
                qs = qs_filter(m.CustomerKarma.objects)
                fields = ["xxxx", "point", "memo1", "customer__name"]
                optimized = self._callFUT(qs, fields)
                self.assertEqual("JOIN" in str(qs.query), has_join)
                with self.assertNumQueries(before_count):
                    customers = [(k.id, k.customer.name, k.point) for k in qs]
                    self.assertEqual(len(customers), 2)
                    self.assertIn("memo3", str(qs.query))

                self.assertIn("JOIN", str(optimized.query))
                with self.assertNumQueries(after_count):
                    customers = [(k.id, k.customer.name, k.point) for k in optimized]
                    self.assertEqual(len(customers), 2)
                    self.assertNotIn("memo3", str(optimized.query))

    def test__one_to_onerel__with_join__rel__star(self):
        # setup
        structure = [
            {"name": "foo", "karma": {"point": 10}},
            {"name": "bar", "karma": {"point": 1}}
        ]
        self._makeCustomerStructure(structure)
        for msg, before_count, after_count, has_join, qs_filter in [
                ("with select related", 1, 1, True, lambda qs: qs.all().select_related("customer")),
                ("without select related", 3, 1, False, lambda qs: qs.all()),
        ]:
            with self.subTest(msg=msg, before_count=before_count, after_count=after_count, has_join=has_join, qs_filter=qs_filter):
                qs = qs_filter(m.CustomerKarma.objects)
                fields = ["*", "customer__*"]
                optimized = self._callFUT(qs, fields)
                self.assertEqual("JOIN" in str(qs.query), has_join)
                with self.assertNumQueries(before_count):
                    customers = [(k.id, k.customer.name, k.point) for k in qs]
                    self.assertEqual(len(customers), 2)
                    self.assertIn("memo3", str(qs.query))

                self.assertIn("JOIN", str(optimized.query))
                with self.assertNumQueries(after_count):
                    customers = [(k.id, k.customer.name, k.point) for k in optimized]
                    self.assertEqual(len(customers), 2)
                    self.assertIn("memo3", str(optimized.query))

    def _makeOrderStructure(self, structure):
        for order_structure in structure:
            order = m.Order.objects.create(name=order_structure["name"])
            for item_strcture in order_structure.get("items", []):
                m.Item.objects.create(order=order, name=item_strcture["name"])

    def test__one_to_many__prefetch(self):
        # setup
        structure = [
            {"name": "foo", "items": [{"name": "x"}, {"name": "y"}]},
            {"name": "bar", "items": [{"name": "x"}, {"name": "y"}]}
        ]
        self._makeOrderStructure(structure)

        fields = ["xxxx", "name", "memo1", "items__name", "items__memo2", "items__yyyy"]
        for msg, before_count, after_count, qs_filter in [
                ("with prefetch related", 2, 2, lambda qs: qs.all().prefetch_related("items")),
                ("without prefetch related", 3, 2, lambda qs: qs.all()),
        ]:
            with self.subTest(msg=msg, before_count=before_count, after_count=after_count, qs_filter=qs_filter):
                qs = qs_filter(m.Order.objects)
                optimized = self._callFUT(qs, fields)

                with self.assertNumQueries(before_count):
                    items = [(o.id, i.id, o.name, i.name) for o in qs for i in o.items.all()]
                    self.assertEqual(len(items), 4)

                with self.assertNumQueries(after_count):
                    items = [(o.id, i.id, o.name, i.name) for o in optimized for i in o.items.all()]
                    self.assertEqual(len(items), 4)

    def test__one_to_many__deprefetch(self):
        # setup
        structure = [
            {"name": "foo", "items": [{"name": "x"}, {"name": "y"}]},
            {"name": "bar", "items": [{"name": "x"}, {"name": "y"}]}
        ]
        self._makeOrderStructure(structure)

        fields = ["xxxx", "name", "memo1"]
        for msg, before_count, after_count, qs_filter in [
                ("with prefetch related", 2, 1, lambda qs: qs.all().prefetch_related("items")),
                ("without prefetch related", 1, 1, lambda qs: qs.all()),
        ]:
            with self.subTest(msg=msg, before_count=before_count, after_count=after_count, qs_filter=qs_filter):
                qs = qs_filter(m.Order.objects)
                optimized = self._callFUT(qs, fields)

                with self.assertNumQueries(before_count):
                    orders = [(o.id, o.name) for o in qs]
                    self.assertEqual(len(orders), 2)

                with self.assertNumQueries(after_count):
                    orders = [(o.id, o.name) for o in optimized]
                    self.assertEqual(len(orders), 2)

    def test__one_to_many__with_join(self):
        # setup
        structure = [
            {"name": "foo", "items": [{"name": "x"}, {"name": "y"}]},
            {"name": "bar", "items": [{"name": "x"}, {"name": "y"}]},
            {"name": "boo", "items": [{"name": "y"}]}
        ]
        self._makeOrderStructure(structure)

        fields = ["xxxx", "name", "memo1", "items__name"]
        for msg, before_count, after_count, qs_filter in [
                ("with prefetch related", 2, 2, lambda qs: qs.all().filter(items__name="x").prefetch_related("items")),
                ("without prefetch related", 3, 2, lambda qs: qs.all().filter(items__name="x")),
        ]:
            with self.subTest(msg=msg, before_count=before_count, after_count=after_count, qs_filter=qs_filter):
                qs = qs_filter(m.Order.objects)
                optimized = self._callFUT(qs, fields)

                self.assertIn("JOIN", str(qs.query))
                with self.assertNumQueries(before_count):
                    items = [(o.id, i.id, o.name, i.name) for o in qs for i in o.items.all()]
                    self.assertEqual(len(items), 4)

                self.assertIn("JOIN", str(optimized.query))
                with self.assertNumQueries(after_count):
                    items = [(o.id, i.id, o.name, i.name) for o in optimized for i in o.items.all()]
                    self.assertEqual(len(items), 4)

    def test__one_to_many__with_dejoin(self):
        # setup
        structure = [
            {"name": "foo", "items": [{"name": "x"}, {"name": "y"}]},
            {"name": "bar", "items": [{"name": "x"}, {"name": "y"}]},
            {"name": "boo", "items": [{"name": "y"}]}
        ]
        self._makeOrderStructure(structure)

        fields = ["xxxx", "name", "memo1"]
        for msg, before_count, after_count, qs_filter in [
                ("with prefetch related", 2, 1, lambda qs: qs.all().filter(items__name="x").prefetch_related("items")),
                ("without prefetch related", 1, 1, lambda qs: qs.all().filter(items__name="x")),
        ]:
            with self.subTest(msg=msg, before_count=before_count, after_count=after_count, qs_filter=qs_filter):
                qs = qs_filter(m.Order.objects)
                optimized = self._callFUT(qs, fields)

                self.assertIn("JOIN", str(qs.query))
                with self.assertNumQueries(before_count):
                    orders = [(o.id, o.name) for o in qs]
                    self.assertEqual(len(orders), 2)

                self.assertIn("JOIN", str(optimized.query))
                with self.assertNumQueries(after_count):
                    orders = [(o.id, o.name) for o in optimized]
                    self.assertEqual(len(orders), 2)

    def test___many_to_one__same_type_multiple(self):
        fields = ["xxxx", "name", "memo1", "customer__name", "substitute__name"]
        qs = m.CustomerPosition.objects.all()
        self.assertNotIn("JOIN", str(qs.query))
        optimized = self._callFUT(qs, fields)
        self.assertIn("JOIN", str(optimized.query))
        # joined query is more long
        # self.assertLess(len(str(optimized.query)), len(str(qs.query)))
        self.assertNotIn("memo3", str(optimized.query))

    # def test___many_to_one__with_join(self):
    #     fields = ["xxxx", "name", "memo1", "order__name", "order__memo2", "order__yyyy"]
    #     qs = m.Item.objects.all().select_related("order")

    #     self.assertIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertIn("JOIN", str(optimized.query))

    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test___many_to_one__without_join(self):
    #     fields = ["xxxx", "name", "memo1"]
    #     qs = m.Item.objects.all().select_related("order")

    #     self.assertIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertNotIn("JOIN", str(optimized.query))
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test___many_to_one__with_join__by_filter(self):
    #     fields = ["xxxx", "name", "memo1"]
    #     qs = m.Item.objects.all().filter(order__name="foo")

    #     self.assertIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertIn("JOIN", str(optimized.query))
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test___many_to_many__with_prefetch(self):
    #     fields = ["xxxx", "name", "memo1", "customers__name", "customers__memo2", "customers__yyyy"]
    #     qs = m.Order.objects.all().prefetch_related("customers")

    #     self.assertNotIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertNotIn("JOIN", str(optimized.query))

    #     self.assertEqual(optimized._prefetch_related_lookups, ["customers"])
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test___many_to_many__without_prefetch(self):
    #     fields = ["xxxx", "name", "memo1"]
    #     qs = m.Order.objects.all().prefetch_related("customers")

    #     self.assertNotIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertNotIn("JOIN", str(optimized.query))

    #     self.assertEqual(optimized._prefetch_related_lookups, [])
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))

    # def test___many_to_many__with_join__by_filter(self):
    #     fields = ["xxxx", "name", "memo1", "customers__memo2"]
    #     qs = m.Order.objects.all().prefetch_related("customers").filter(customers__name="foo")

    #     self.assertIn("JOIN", str(qs.query))
    #     optimized = self._callFUT(qs, fields)
    #     self.assertIn("JOIN", str(optimized.query))
    #     self.assertLess(len(str(optimized.query)), len(str(qs.query)))
    #     self.assertNotIn("memo3", str(optimized.query))
