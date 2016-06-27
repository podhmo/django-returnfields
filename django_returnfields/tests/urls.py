from django.conf.urls import url, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns  # NOQA
from rest_framework import routers
from . import viewsets

router = routers.DefaultRouter()
router.register(r'users', viewsets.UserViewSet)
router.register(r'users2', viewsets.UserViewSet2)
router.register(r'skill_users', viewsets.SkillUserViewSet)
router.register(r'group_users', viewsets.GroupUserViewSet)
router.register(r'skills', viewsets.SkillViewSet)

urlpatterns = [
    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]
urlpatterns += staticfiles_urlpatterns()
