# -*- coding:utf-8 -*-
import json
import unittest
from rest_framework import serializers


class Comment(object):
    def __init__(self, name, content):
        self.name = name
        self.content = content


class Article(object):
    def __init__(self, name, content, comments):
        self.name = name
        self.content = content
        self.comments = comments


class SerializerDumpTests(unittest.TestCase):
    def _makeOne(self, serializer_class):
        from django_returnfields import serializer_factory
        return serializer_factory(serializer_class)

    def _makeArticle(self):
        name = "hello"
        content = "hello world"
        comments = [Comment("title{}".format(i), "hmm") for i in range(3)]
        return Article(name, content, comments)

    def _makeDummyRequest(self, d):
        class request:
            GET = d
        return request

    def _makeSerializer(self):
        class CommentSerializer(serializers.Serializer):
            name = serializers.CharField()
            content = serializers.CharField()

        class ArticleSerializer(serializers.Serializer):
            name = serializers.CharField()
            content = serializers.CharField()
            comments = CommentSerializer(many=True)
        return ArticleSerializer

    def test_it(self):
        Serializer = self._makeOne(self._makeSerializer())
        article = self._makeArticle()
        result = Serializer(article).data

        expected = '{"name": "hello", "content": "hello world", "comments": [{"name": "title0", "content": "hmm"}, {"name": "title1", "content": "hmm"}, {"name": "title2", "content": "hmm"}]}'  # NOQA
        actual = json.dumps(result)
        self.assertEqual(actual, expected)

    def test_it__filtering(self):
        Serializer = self._makeOne(self._makeSerializer())
        article = self._makeArticle()
        request = self._makeDummyRequest({"skip_fields": "content,comments__content"})
        result = Serializer(article, context={"request": request}).data

        expected = '{"name": "hello", "comments": [{"name": "title0"}, {"name": "title1"}, {"name": "title2"}]}'  # NOQA
        actual = json.dumps(result)
        self.assertEqual(actual, expected)

    def test_it__filtering__from_list__cached(self):
        Serializer = self._makeOne(self._makeSerializer())

        articles = [self._makeArticle(), self._makeArticle(), self._makeArticle()]
        request = self._makeDummyRequest({"skip_fields": "content,comments__content"})
        result = Serializer(articles, context={"request": request}, many=True).data
        expected = '[{"name": "hello", "comments": [{"name": "title0"}, {"name": "title1"}, {"name": "title2"}]}, {"name": "hello", "comments": [{"name": "title0"}, {"name": "title1"}, {"name": "title2"}]}, {"name": "hello", "comments": [{"name": "title0"}, {"name": "title1"}, {"name": "title2"}]}]'  # NOQA

        actual = json.dumps(result)
        self.assertEqual(actual, expected)
