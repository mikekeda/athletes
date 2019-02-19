class RemoteAddrMiddleware:
    """
    Middleware to set REMOTE_ADDR header for dj-stripe,
    Gunicorn is bound to a UNIX socket so REMOTE_ADDR is always empty
    http://docs.gunicorn.org/en/stable/deploy.html
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.META.get("REMOTE_ADDR") and \
                request.META.get("HTTP_X_FORWARDED_FOR"):
            request.META["REMOTE_ADDR"] = request.META["HTTP_X_FORWARDED_FOR"]

        response = self.get_response(request)

        return response
