from django.contrib import messages
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
            messages.add_message(request, messages.ERROR, "Could not reach libvirt host")
            return redirect(request.META.get("HTTP_REFERER", "/"))

