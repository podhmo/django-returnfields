import json


def do_get(client, msg, path):
    print(msg)
    print("```")
    print("request: GET {}".format(path))
    response = client.get(path)
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))
    print("```")


def main(client):
    do_get(client, "one", "/internal/blog/1/?return_fields=articles&aggressive=1")
    do_get(client, "all", "/internal/blog/?return_fields=articles&aggressive=1")
