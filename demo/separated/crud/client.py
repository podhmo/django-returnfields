def main(client):
    """call view via Client"""
    import json

    # success request
    path = "/users/"
    print("========================================")
    print("request: GET {}".format(path))
    response = client.get(path)
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))

    path = "/users/"
    print("========================================")
    print("request: POST {}".format(path))
    response = client.post(path, {"username": "foo"})
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))
    path = "/skills/"

    print("========================================")
    print("request: POST {}".format(path))
    response = client.post(path, {"user": 1, "name": "magic"})
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))
    print("========================================")
    print("request: POST {}".format(path))
    response = client.post(path, {"user": 1, "name": "magik"})
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))

    path = "/users/1/?format=json"
    response = client.get(path)
    print("========================================")
    print("request: GET {}".format(path))
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))

    path = "/users/1/?format=json&return_fields=username,id"
    response = client.get(path)
    print("========================================")
    print("request: GET {}".format(path))
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))

    path = "/users/1/?format=json&return_fields=username,skills&skip_fields=skills__id,skills__user"
    response = client.get(path)
    print("========================================")
    print("request: GET {}".format(path))
    print("status code: {response.status_code}".format(response=response))
    print("response: {content}".format(content=json.dumps(response.data, indent=2)))
