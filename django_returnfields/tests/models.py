# -*- coding:utf-8 -*-
from django.db import models
from django.contrib.auth.models import User


class Group(models.Model):
    name = models.CharField(max_length=255, default="", null=False)
    user = models.ForeignKey(User, null=False)
