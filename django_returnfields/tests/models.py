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
