## how to use this

```bash
$ python app.py --run-server  # running as server app
$ python app.py  # access simulation via django client
```

## output(output of simulation)

listing (empty)
```
request: GET /users/
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."username", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined" FROM "auth_user"; args=()
status code: 200
response: []
```
create user (name=foo)
```
request: POST /users/
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT (1) AS "a" FROM "auth_user" WHERE "auth_user"."username" = 'foo' LIMIT 1; args=('foo',)
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) BEGIN; args=None
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) INSERT INTO "auth_user" ("password", "last_login", "is_superuser", "username", "first_name", "last_name", "email", "is_staff", "is_active", "date_joined") VALUES ('', NULL, 0, 'foo', '', '', '', 0, 1, '2016-07-09 21:24:57.632210'); args=['', None, False, 'foo', '', '', '', False, True, '2016-07-09 21:24:57.632210']
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "crud_skill"."id", "crud_skill"."name", "crud_skill"."user_id" FROM "crud_skill" WHERE "crud_skill"."user_id" = 1; args=(1,)
status code: 201
response: {
  "id": 1,
  "url": "http://testserver/users/1/",
  "username": "foo",
  "email": "",
  "is_staff": false,
  "skills": []
}
```
create user (name=bar)
```
request: POST /users/
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT (1) AS "a" FROM "auth_user" WHERE "auth_user"."username" = 'bar' LIMIT 1; args=('bar',)
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) BEGIN; args=None
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) INSERT INTO "auth_user" ("password", "last_login", "is_superuser", "username", "first_name", "last_name", "email", "is_staff", "is_active", "date_joined") VALUES ('', NULL, 0, 'bar', '', '', '', 0, 1, '2016-07-09 21:24:57.644955'); args=['', None, False, 'bar', '', '', '', False, True, '2016-07-09 21:24:57.644955']
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "crud_skill"."id", "crud_skill"."name", "crud_skill"."user_id" FROM "crud_skill" WHERE "crud_skill"."user_id" = 2; args=(2,)
status code: 201
response: {
  "id": 2,
  "url": "http://testserver/users/2/",
  "username": "bar",
  "email": "",
  "is_staff": false,
  "skills": []
}
```
create skill for user(id=1) (name=magic)
```
request: POST /skills/
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."username", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined" FROM "auth_user" WHERE "auth_user"."id" = 1; args=(1,)
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) BEGIN; args=None
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) INSERT INTO "crud_skill" ("name", "user_id") VALUES ('magic', 1); args=['magic', 1]
status code: 201
response: {
  "id": 1,
  "user": 1,
  "name": "magic"
}
```
create skill for user(id=1) (name=magik)
```
request: POST /skills/
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."username", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined" FROM "auth_user" WHERE "auth_user"."id" = 1; args=(1,)
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) BEGIN; args=None
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) INSERT INTO "crud_skill" ("name", "user_id") VALUES ('magik', 1); args=['magik', 1]
status code: 201
response: {
  "id": 2,
  "user": 1,
  "name": "magik"
}
```
create skill for user(id=2) (name=magic)
```
request: POST /skills/
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."username", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined" FROM "auth_user" WHERE "auth_user"."id" = 2; args=(2,)
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) BEGIN; args=None
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) INSERT INTO "crud_skill" ("name", "user_id") VALUES ('magic', 2); args=['magic', 2]
status code: 201
response: {
  "id": 3,
  "user": 2,
  "name": "magic"
}
```
create skill for user(id=2) (name=magik)
```
request: POST /skills/
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."username", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined" FROM "auth_user" WHERE "auth_user"."id" = 2; args=(2,)
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) BEGIN; args=None
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) INSERT INTO "crud_skill" ("name", "user_id") VALUES ('magik', 2); args=['magik', 2]
status code: 201
response: {
  "id": 4,
  "user": 2,
  "name": "magik"
}
```
show information for user(id=1)
```
request: GET /users/1/?format=json
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."username", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined" FROM "auth_user" WHERE "auth_user"."id" = 1; args=(1,)
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "crud_skill"."id", "crud_skill"."name", "crud_skill"."user_id" FROM "crud_skill" WHERE "crud_skill"."user_id" = 1; args=(1,)
status code: 200
response: {
  "id": 1,
  "url": "http://testserver/users/1/?format=json",
  "username": "foo",
  "email": "",
  "is_staff": false,
  "skills": [
    {
      "id": 1,
      "user": 1,
      "name": "magic"
    },
    {
      "id": 2,
      "user": 1,
      "name": "magik"
    }
  ]
}
```
show information for user(id=1), only id, username
```
request: GET /users/1/?format=json&return_fields=username,id
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."username", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined" FROM "auth_user" WHERE "auth_user"."id" = 1; args=(1,)
status code: 200
response: {
  "id": 1,
  "username": "foo"
}
```
show information for user(id=1), with skills (but filtered)
```
request: GET /users/?format=json&return_fields=username,skills&skip_fields=skills__id,skills__user
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "auth_user"."id", "auth_user"."password", "auth_user"."last_login", "auth_user"."is_superuser", "auth_user"."username", "auth_user"."first_name", "auth_user"."last_name", "auth_user"."email", "auth_user"."is_staff", "auth_user"."is_active", "auth_user"."date_joined" FROM "auth_user"; args=()
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "crud_skill"."id", "crud_skill"."name", "crud_skill"."user_id" FROM "crud_skill" WHERE "crud_skill"."user_id" = 1; args=(1,)
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "crud_skill"."id", "crud_skill"."name", "crud_skill"."user_id" FROM "crud_skill" WHERE "crud_skill"."user_id" = 2; args=(2,)
status code: 200
response: [
  {
    "username": "foo",
    "skills": [
      {
        "name": "magic"
      },
      {
        "name": "magik"
      }
    ]
  },
  {
    "username": "bar",
    "skills": [
      {
        "name": "magic"
      },
      {
        "name": "magik"
      }
    ]
  }
]
```
show information for user(id=1), with skills (but filtered) -- aggressive
```
request: GET /users/?format=json&aggressive=1&return_fields=username,skills&skip_fields=skills__id,skills__user
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "auth_user"."id", "auth_user"."username" FROM "auth_user"; args=()
[2016-07-09 21:24:57][django.db.backends:L89:DEBUG] (0.000) SELECT "crud_skill"."id", "crud_skill"."name", "crud_skill"."user_id" FROM "crud_skill" WHERE "crud_skill"."user_id" IN (2, 1); args=(2, 1)
status code: 200
response: [
  {
    "username": "bar",
    "skills": [
      {
        "name": "magic"
      },
      {
        "name": "magik"
      }
    ]
  },
  {
    "username": "foo",
    "skills": [
      {
        "name": "magic"
      },
      {
        "name": "magik"
      }
    ]
  }
]
```
