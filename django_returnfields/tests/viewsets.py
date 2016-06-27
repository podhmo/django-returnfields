# -*- coding:utf-8 -*-
from .models import User
from rest_framework import viewsets
from rest_framework import pagination

from django_returnfields import serializer_factory, restriction_factory

from . import serializers
from .models import Skill


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializer_factory(serializers.UserSerializer)


class SkillUserPaginatedViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializer_factory(serializers.SkillUserSerializer)

    class MiniPagination(pagination.PageNumberPagination):
        page_size = 5
        page_size_query_param = 'page_size'
        max_page_size = 1000

    pagination_class = MiniPagination


class UserViewSet2(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializer_factory(
        serializers.UserSerializer,
        restriction=restriction_factory(include_key="include", exclude_key="exclude"))


class SkillUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializer_factory(serializers.SkillUserSerializer)


class GroupUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializer_factory(serializers.GroupUserSerializer)


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = serializer_factory(serializers.SkillSerializer)
