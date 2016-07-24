from django.conf.urls import url, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from rest_framework import routers
from . import viewsets

router = routers.DefaultRouter()

router.register(r'/blog', viewsets.BlogViewSet)
router.register(r'/article', viewsets.ArticleViewSet)
router.register(r'/comment', viewsets.CommentViewSet)
router.register(r'/category', viewsets.CategoryViewSet)

urlpatterns = [
    url(r'^internal', include(router.urls))
]
urlpatterns += staticfiles_urlpatterns()
