# -*- coding:utf-8 -*-
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User


def extract_error_message(response):
    # this is utility function, when test is failed
    return getattr(response, "data", None) or response.content


class RestrictFeatureTests(APITestCase):
    # see: ./url:UserViewSet.serializer_class

    def setUp(self):
        super().setUp()
        self.login_user = User.objects.create_superuser('admin', 'myemail@test.com', '')
        self.client.force_authenticate(self.login_user)

    def test_restricted(self):
        path = "/api/users/?return_fields=username,url"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"url", "username"})

    def test_restricted2(self):
        path = "/api/users/?return_fields=username, url, is_staff"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"url", "username", "is_staff"})

    def test_restricted__invalid_names(self):
        path = "/api/users/?return_fields=username, xxxx"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"username"})

    def test_restricted__another_name(self):
        path = "/api/users2/?include=username"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"username"})

    def test_restricted__another_name__default_include_keys_are_ignored(self):
        path = "/api/users2/?return_fields=username"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertNotEqual(set(response.data[0].keys()), {"username"})


class PlainActionTests(APITestCase):
    def setUp(self):
        super().setUp()
        self.login_user = User.objects.create_superuser('admin', 'myemail@test.com', '')
        self.client.force_authenticate(self.login_user)

    def test_listing(self):
        path = "/api/users/"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(len(response.data), 1, msg=response.data)
        self.assertEqual(set(response.data[0].keys()), {"url", "username", "is_staff", "email"})

    def test_listingwith_another_user(self):
        User.objects.create_user('another', 'myemail@test.com', '')
        path = "/api/users/"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(len(response.data), 2, msg=response.data)

    def test_create(self):
        self.assertEqual(User.objects.count(), 1)
        path = "/api/users/"
        data = {"username": "another", "password": "hmm", "email": "myemail+another@test.com"}
        response = self.client.post(path, format="json", data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, msg=extract_error_message(response))

        self.assertEqual(User.objects.count(), 2)

    def test_update(self):
        self.assertEqual(User.objects.count(), 1)
        path = "/api/users/{}/".format(self.login_user.id)
        data = {"username": "another"}
        response = self.client.patch(path, format="json", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))

        self.assertEqual(User.objects.get(id=self.login_user.id).username, "another")

    def test_delete(self):
        self.assertEqual(User.objects.count(), 1)
        path = "/api/users/{}/".format(self.login_user.id)
        data = {"username": "another"}
        response = self.client.delete(path, format="json", data=data)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT, msg=extract_error_message(response))

        self.assertEqual(User.objects.count(), 0)
