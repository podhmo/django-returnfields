# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group  # NOQA


class User(AbstractUser):
    pass


class Skill(models.Model):
    name = models.CharField(max_length=255, default="", null=False)
    user = models.ForeignKey(User, null=False, related_name="skills")


class Permission(models.Model):
    group = models.ForeignKey(Group, null=False, related_name="permissions")


# self defined.
# relation: CustomerKarma - Customer *-* Order -* Item
class Customer(models.Model):
    name = models.CharField(max_length=255, default="", null=False)
    memo1 = models.CharField(max_length=255, default="", null=False)  # for test
    memo2 = models.CharField(max_length=255, default="", null=False)  # for test
    memo3 = models.CharField(max_length=255, default="", null=False)  # for test

    class Meta:
        db_table = "customer"


class CustomerKarma(models.Model):
    point = models.IntegerField(null=False, default=0)
    customer = models.OneToOneField(Customer, related_name="karma")
    memo1 = models.CharField(max_length=255, default="", null=False)  # for test
    memo2 = models.CharField(max_length=255, default="", null=False)  # for test
    memo3 = models.CharField(max_length=255, default="", null=False)  # for test

    class Meta:
        db_table = "customerkarma"


class CustomerPosition(models.Model):
    customer = models.ForeignKey(Customer)
    substitute = models.ForeignKey(Customer)
    name = models.CharField(max_length=255, default="", null=False)
    memo1 = models.CharField(max_length=255, default="", null=False)  # for test
    memo2 = models.CharField(max_length=255, default="", null=False)  # for test
    memo3 = models.CharField(max_length=255, default="", null=False)  # for test

    class Meta:
        db_table = "customerposition"


class Order(models.Model):
    customers = models.ManyToManyField(Customer, related_name="orders")
    name = models.CharField(max_length=255, default="", null=False)
    price = models.IntegerField(null=False, default=0)
    memo1 = models.CharField(max_length=255, default="", null=False)  # for test
    memo2 = models.CharField(max_length=255, default="", null=False)  # for test
    memo3 = models.CharField(max_length=255, default="", null=False)  # for test

    class Meta:
        db_table = "order"


class Item(models.Model):
    order = models.ForeignKey(Order, related_name="items")
    name = models.CharField(max_length=255, default="", null=False)
    price = models.IntegerField(null=False, default=0)
    memo1 = models.CharField(max_length=255, default="", null=False)  # for test
    memo2 = models.CharField(max_length=255, default="", null=False)  # for test
    memo3 = models.CharField(max_length=255, default="", null=False)  # for test

    class Meta:
        db_table = "item"
