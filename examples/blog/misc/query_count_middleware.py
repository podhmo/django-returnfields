import time
from django.conf import settings
from django.db import connections


class QueryCountMiddleware:
    def process_request(self, request):
        if settings.DEBUG:
            request.timestamp = time.time()
            c = connections["default"]
            c.queries_log.clear()

    def process_response(self, request, response):
        if settings.DEBUG and hasattr(response, "data"):
            response.timestamp = time.time()
            response.total_time = response.timestamp - request.timestamp
            c = connections["default"]
            response.query_count = len(c.queries_log)
            meta = {
                "total_time": response.timestamp - request.timestamp,
                "query_count": response.query_count
            }
            if isinstance(response.data, list):
                for subdata in response.data:
                    subdata["meta"] = meta
            elif isinstance(response.data, dict):
                response.data["meta"] = meta
            print("type", type(response.data), "@@", meta)
        return response
