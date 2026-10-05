"""How long the server took, on every response, for the on-phone readout (static/js/perf.js).

The ``Server-Timing`` header carries three figures: the whole request, the time spent
waiting for queries with their count, and the time spent opening a database connection.
It only measures. It reads no request data and changes no response body.
"""

import time

from django.db import connection


class ServerTiming:
    """Placed first, so the figures cover every other middleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        count, waited, opening = 0, 0.0, 0.0

        def timed(execute, sql, params, many, context):
            nonlocal count, waited
            start = time.perf_counter()
            try:
                return execute(sql, params, many, context)
            finally:
                count += 1
                waited += time.perf_counter() - start

        # A query opens the connection before it runs, so opening is timed where it happens.
        # The attribute shadows the method on this thread's connection for this request only.
        open_connection = connection.connect

        def connect():
            nonlocal opening
            start = time.perf_counter()
            try:
                open_connection()
            finally:
                opening += time.perf_counter() - start

        start = time.perf_counter()
        connection.connect = connect
        try:
            with connection.execute_wrapper(timed):
                response = self.get_response(request)
        finally:
            del connection.connect
        total = time.perf_counter() - start
        response["Server-Timing"] = (
            f"app;dur={total * 1000:.1f}, "
            f'db;dur={waited * 1000:.1f};desc="{count} quer{"y" if count == 1 else "ies"}", '
            f"connect;dur={opening * 1000:.1f}"
        )
        return response
