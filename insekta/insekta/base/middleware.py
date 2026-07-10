from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect

class ExceptionHandlingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        from insekta.remoteapi.client import RemoteApiError
        if isinstance(exception, RemoteApiError):
            # AJAX callers handle the error themselves, otherwise the message will be swallowed
            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                return HttpResponse(status=503)
            messages.add_message(request, messages.ERROR, "Could not reach libvirt host")
            return redirect(request.META.get("HTTP_REFERER", "/"))

