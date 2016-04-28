from django.conf.urls import url, include
from django.contrib.auth.models import User
from django.contrib.staticfiles.urls import staticfiles_urlpatterns  # NOQA
from rest_framework import routers, serializers, viewsets


from django_returnfields import return_fields_serializer_factory, Restriction


# Serializers define the API representation.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'is_staff')


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = return_fields_serializer_factory(UserSerializer)


class UserViewSet2(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = return_fields_serializer_factory(UserSerializer, restriction=Restriction(include_key="include"))

# Routers provide an easy way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'users2', UserViewSet2)

urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
urlpatterns += staticfiles_urlpatterns()

ROOT_URLCONF = 'booklista_sns.urls'
# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
