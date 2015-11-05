from django.shortcuts import redirect

from insekta.ethics import views


class EthicsMiddleware:
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated() and not request.user.accepted_ethics:
            if view_func not in (views.view_ethics, views.view_arguments):
                return redirect('ethics:view')
        return None
