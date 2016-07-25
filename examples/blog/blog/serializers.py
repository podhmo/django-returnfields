from . import models
from django_returnfields import serializer_factory
from rest_framework import serializers


@serializer_factory
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Category
        fields = "__all__"
        readonly_fields = ("ctime", "utime")


@serializer_factory
class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Comment
        fields = "__all__"
        readonly_fields = ("ctime", "utime")


@serializer_factory
class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Article
        fields = "__all__"
        readonly_fields = ("ctime", "utime")


@serializer_factory
class BlogSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Blog
        fields = "__all__"
        readonly_fields = ("ctime", "utime")


@serializer_factory
class CategoryFullSetSerializer(CategorySerializer):
    pass


@serializer_factory
class CommentFullSetSerializer(CommentSerializer):
    pass


@serializer_factory
class ArticleFullSetSerializer(ArticleSerializer):
    comments = CommentFullSetSerializer(many=True)
    categories = CategorySerializer(many=True)


@serializer_factory
class BlogFullSetSerializer(BlogSerializer):
    articles = ArticleFullSetSerializer(many=True)
