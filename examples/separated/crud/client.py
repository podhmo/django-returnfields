import json


def do_get(client, msg, path):
    print(msg)
    print("```")
    print("request: GET {}".format(path))
    response = client.get(path)
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))
    print("```")


def do_post(client, msg, path, data):
    print(msg)
    print("```")
    print("request: POST {}".format(path))
    response = client.post(path, data)
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))
    print("```")


def main(client):
    """call view via Client"""
    # success request
    msg = "listing (empty)"
    do_get(client, msg, "/users/")

    msg = "create user (name=foo)"
    do_post(client, msg, "/users/", {"username": "foo"})
    msg = "create user (name=bar)"
    do_post(client, msg, "/users/", {"username": "bar"})

    msg = "create skill for user(id=1) (name=magic)"
    do_post(client, msg, "/skills/", {"user": 1, "name": "magic"})
    msg = "create skill for user(id=1) (name=magik)"
    do_post(client, msg, "/skills/", {"user": 1, "name": "magik"})

    msg = "create skill for user(id=2) (name=magic)"
    do_post(client, msg, "/skills/", {"user": 2, "name": "magic"})
    msg = "create skill for user(id=2) (name=magik)"
    do_post(client, msg, "/skills/", {"user": 2, "name": "magik"})

    msg = "show information for user(id=1)"
    do_get(client, msg, "/users/1/?format=json")

    msg = "show information for user(id=1), only id, username"
    do_get(client, msg, "/users/1/?format=json&return_fields=username,id")

    msg = "show information for user(id=1), with skills (but filtered)"
    do_get(client, msg, "/users/?format=json&return_fields=username,skills&skip_fields=skills__id,skills__user")

    msg = "show information for user(id=1), with skills (but filtered) -- aggressive"
    do_get(client, msg, "/users/?format=json&aggressive=1&return_fields=username,skills&skip_fields=skills__id,skills__user")
