from django.shortcuts import redirect, render


def index(request):
    if request.user.is_authenticated:
        return redirect('scenarios:index')
    return render(request, 'base/index.html')
