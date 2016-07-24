# -*- coding:utf-8 -*-
from django.db import models
from django.utils import timezone


class HasTimestampModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Blog(HasTimestampModel):
    title = models.CharField(max_length=255)

    class Meta:
        db_table = "blog"


class Article(HasTimestampModel):
    title = models.CharField(max_length=255)
    content = models.TextField(default="", blank=True)
    blog = models.ForeignKey(Blog, related_name="articles")

    class Meta:
        db_table = "article"


class Comment(HasTimestampModel):
    title = models.CharField(max_length=255)  # user name?
    content = models.TextField(default="", blank=True)
    article = models.ForeignKey(Article, related_name="comments")

    class Meta:
        db_table = "comment"


class Category(HasTimestampModel):
    name = models.CharField(max_length=255)
    articles = models.ManyToManyField(Article, related_name="categories")

    class Meta:
        db_table = "category"
