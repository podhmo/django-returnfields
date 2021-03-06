# -*- coding:utf-8 -*-
from unittest import mock
from rest_framework.test import APITestCase
from rest_framework import status
from .models import User


def extract_error_message(response):
    # this is utility function, when test is failed
    return getattr(response, "data", None) or response.content


class RestrictFeatureTests(APITestCase):
    # see: ./url:UserViewSet.serializer_class

    def setUp(self):
        super(RestrictFeatureTests, self).setUp()
        self.login_user = User.objects.create_superuser('admin', 'myemail@test.com', '')
        self.client.force_authenticate(self.login_user)

    def test_restricted(self):
        path = "/api/users/?return_fields=username,url"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"url", "username"})

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

    def test_restricted__exclude(self):
        path = "/api/users/?skip_fields=username,url,email"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"id", "is_staff"})


class NestedRestrictFeatureTests(APITestCase):
    # see: ./url:UserViewSet.serializer_class

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_superuser('admin', 'myemail@test.com', '')
        from .models import Skill
        Skill.objects.bulk_create([Skill(user=user, name="magic"), Skill(user=user, name="magik")])

    def test_no_filtering(self):
        path = "/api/skills/"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"id", "user", "name"})
        self.assertEqual(set(response.data[0]["user"].keys()), {"id", "url", "username", "is_staff", "email"})

    def test_same_keys(self):
        path = "/api/skills/?return_fields=user, id"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"id", "user"})
        self.assertEqual(set(response.data[0]["user"].keys()), {"id", "url", "username", "is_staff", "email"})

    def test_nested__all(self):
        path = "/api/skills/?return_fields=user"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"user"})
        self.assertEqual(set(response.data[0]["user"].keys()), {"id", "url", "username", "is_staff", "email"})

    def test_nested__all__with_noise(self):
        path = "/api/skills/?return_fields=user, user__id, xxxx"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"user"})
        self.assertEqual(set(response.data[0]["user"].keys()), {"id", "url", "username", "is_staff", "email"})

    def test_nested__specific(self):
        path = "/api/skills/?return_fields=user__id"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"user"})
        self.assertEqual(set(response.data[0]["user"].keys()), {"id"})

    def test_nested__many__no_filtering(self):
        path = "/api/skill_users/"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"id", "skills", "username"})
        self.assertEqual(set(response.data[0]["skills"][0].keys()), {"id", "name"})

    def test_nested__many(self):
        path = "/api/skill_users/?return_fields=skills__name,username"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"skills", "username"})
        self.assertEqual(set(response.data[0]["skills"][0].keys()), {"name"})

    def test_nested__many__exclude(self):
        path = "/api/skill_users/?return_fields=skills&skip_fields=skills__id"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"skills"})
        self.assertEqual(set(response.data[0]["skills"][0].keys()), {"name"})


class AggressiveFeatureTests(APITestCase):
    # see: ./url:GroupUserViewSet.serializer_class
    @classmethod
    def setUpTestData(cls):
        from .models import Group, Permission
        user = User.objects.create_superuser('admin', 'myemail@test.com', '')
        group = Group.objects.create(name="magic")
        group2 = Group.objects.create(name="magik")
        group3 = Group.objects.create(name="magick")
        Permission.objects.create(group=group)
        Permission.objects.create(group=group)
        Permission.objects.create(group=group2)
        group.user_set.add(user)
        group.user_set.add(User.objects.create_superuser('another', 'myemail2@test.com', ''))
        group2.user_set.add(user)
        group3.user_set.add(user)
        group.save()
        group2.save()

    def test_include__aggressive(self):
        path = "/api/group_users/?return_fields=id&aggressive=1"
        with self.assertNumQueries(1):
            response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"id"})

    def test_exclude__aggressive(self):
        path = "/api/group_users/?skip_fields=id&aggressive=1"
        with self.assertNumQueries(3):
            response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"username", "groups"})
        self.assertEqual(set(response.data[0]["groups"][0].keys()), {"name", "id", "permissions"})

    def test_include__relation__aggressive(self):
        path = "/api/group_users/?return_fields=id,groups&aggressive=1"
        with self.assertNumQueries(3):
            response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"id", "groups"})
        self.assertEqual(set(response.data[0]["groups"][0].keys()), {"name", "id", "permissions"})

    def test_exclude__relation__aggressive(self):
        path = "/api/group_users/?skip_fields=id,groups&aggressive=1"
        with self.assertNumQueries(1):
            response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"username"})

    def test_include__related_field__aggressive(self):
        path = "/api/group_users/?return_fields=id,groups__name&aggressive=1"
        with self.assertNumQueries(2):
            response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"id", "groups"})
        self.assertEqual(set(response.data[0]["groups"][0].keys()), {"name"})

    def test_exclude__related_field__aggressive(self):
        path = "/api/group_users/?skip_fields=id,groups__name&aggressive=1"
        with self.assertNumQueries(3):
            response = self.client.get(path, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"username", "groups"})
        self.assertEqual(set(response.data[0]["groups"][0].keys()), {"id", "permissions"})

    def test_both__related_field__aggressive(self):
        path = "/api/group_users/?return_fields=groups__*,groups&skip_fields=id,groups__permissions&aggressive=1"
        with self.assertNumQueries(2):
            response = self.client.get(path, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(set(response.data[0].keys()), {"groups"})
        self.assertEqual(set(response.data[0]["groups"][0].keys()), {"id", "name"})

    def test_detail__aggressive(self):
        path = "/api/group_users/1/?aggressive=1"
        with self.assertNumQueries(4):  # 3 = user -> groups -> permissions
            response = self.client.get(path, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
            # todo: response check


class PaginatedViewTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        from .models import Skill
        for i in range(6):
            user = User.objects.create_superuser('admin{}'.format(i), 'myemail{}@test.com'.format(i), '')
            Skill.objects.bulk_create([
                Skill(user=user, name="dummy"), Skill(user=user, name="magic"), Skill(user=user, name="magik")
            ])

    def test_listing__without_paramater__feature_is_deactivated(self):
        path = "/api/paginated/skill_users/?page_size=5"
        with self.assertNumQueries(7):
            with mock.patch("django_returnfields.optimize.aggressive.aggressive_query") as m:
                m.side_effect = AssertionError("don't call it!")
                response = self.client.get(path, format="json")

            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
            self.assertEqual(set(response.data.keys()), set(['count', 'next', 'previous', 'results']))

            self.assertEqual(len(response.data["results"]), 5)
            self.assertEqual(set(response.data["results"][0].keys()), {'id', 'skills', 'username'})
            self.assertEqual(len(response.data["results"][0]["skills"]), 3)  # dummy, magic, magik
            self.assertEqual(set(response.data["results"][0]["skills"][0].keys()), {"id", "name"})

    def test_listing__pagination(self):
        path = "/api/paginated/skill_users/?aggressive=1&page_size=5"
        with self.assertNumQueries(4, msg="*auto prefetch/join"):
            response = self.client.get(path, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
            self.assertEqual(set(response.data.keys()), set(['count', 'next', 'previous', 'results']))

            self.assertEqual(len(response.data["results"]), 5, msg="*paginated")
            self.assertEqual(set(response.data["results"][0].keys()), {'id', 'skills', 'username'})

            self.assertEqual(len(response.data["results"][0]["skills"]), 2, "*prefetch_filter() is activated")
            self.assertEqual(set(response.data["results"][0]["skills"][0].keys()), {"id", "name"})

    def test_listing__pagination__with_skip(self):
        path = "/api/paginated/skill_users/?aggressive=1&page_size=5&skip_fields=skills"
        with self.assertNumQueries(3):
            response = self.client.get(path, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
            self.assertEqual(set(response.data.keys()), set(['count', 'next', 'previous', 'results']))

            self.assertEqual(len(response.data["results"]), 5)
            self.assertEqual(set(response.data["results"][0].keys()), {'id', 'username'})

    def test_listing__pagination__with_skip2(self):
        path = "/api/paginated/skill_users/?aggressive=1&page_size=5&skip_fields=skills__id,skills__name"
        with self.assertNumQueries(4):
            response = self.client.get(path, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
            self.assertEqual(set(response.data.keys()), set(['count', 'next', 'previous', 'results']))

            self.assertEqual(len(response.data["results"]), 5)
            self.assertEqual(set(response.data["results"][0].keys()), {'id', 'skills', 'username'})
            self.assertEqual(set(response.data["results"][0]["skills"][0].keys()), set())

    def test_listing__pagination__ordered(self):
        path = "/api/paginated/skill_users/?aggressive=1&page_size=5&ordering=-id&return_fields=id"
        with self.assertNumQueries(3):
            response = self.client.get(path, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
            self.assertEqual(set(response.data.keys()), set(['count', 'next', 'previous', 'results']))

            self.assertEqual(len(response.data["results"]), 5)
            self.assertEqual([u["id"]for u in response.data['results']], [6, 5, 4, 3, 2], msg="*order by id desc")


class ForceAggressivePaginatedViewTests(APITestCase):
    @classmethod
    def setUpTestData(self):
        from .models import Skill
        for i in range(3):
            user = User.objects.create_superuser('admin{}'.format(i), 'myemail{}@test.com'.format(i), '')
            Skill.objects.bulk_create([
                Skill(user=user, name="dummy"), Skill(user=user, name="magic"), Skill(user=user, name="magik")
            ])

    def test_with_aggressive_parameter(self):
        path = "/api/force_aggressive/skill_users/?aggressive=1"
        with self.assertNumQueries(2):
            response = self.client.get(path, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
            self.assertEqual(len(response.data), 3)
            self.assertEqual(set(response.data[0].keys()), {"id", "skills", "username"})

    def test_without_aggressive_parameter(self):
        path = "/api/force_aggressive/skill_users/"
        with self.assertNumQueries(2):
            response = self.client.get(path, format="json")
            self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
            self.assertEqual(len(response.data), 3)
            self.assertEqual(set(response.data[0].keys()), {"id", "skills", "username"})


class PlainCRUDActionTests(APITestCase):
    def setUp(self):
        super(PlainCRUDActionTests, self).setUp()
        self.login_user = User.objects.create_superuser('admin', 'myemail@test.com', '')
        self.client.force_authenticate(self.login_user)

    def test_listing(self):
        path = "/api/users/"
        response = self.client.get(path, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=extract_error_message(response))
        self.assertEqual(len(response.data), 1, msg=response.data)
        self.assertEqual(set(response.data[0].keys()), {"id", "url", "username", "is_staff", "email"})

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
