from django.conf.urls import url, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from rest_framework import routers
from .viewsets import UserViewSet, SkillViewSet

router = routers.DefaultRouter()

router.register(r'users', UserViewSet)
router.register(r'skills', SkillViewSet)

urlpatterns = [
    url(r'^', include(router.urls))
]
urlpatterns += staticfiles_urlpatterns()

