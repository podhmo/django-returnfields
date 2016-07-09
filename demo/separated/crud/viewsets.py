from rest_framework import viewsets
from .models import User, Skill
from .serializers import UserSerializer, SkillSerializer
from django_returnfields import serializer_factory  # this!!


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializer_factory(UserSerializer)


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = serializer_factory(SkillSerializer)

