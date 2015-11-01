from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required


@login_required
def view_ethics(request):
    disagreed = False

    next = request.GET.get('next', '/')
    if request.method == 'POST':
        if 'accept' in request.POST:
            request.user.accepted_ethics = True
            request.user.save()
            if not next.startswith('/'):
                next = '/'
            return redirect(next)
        else:
            disagreed = True

    return render(request, 'ethics/view_ethics.html', {
        'disagreed': disagreed,
        'next': next
    })


@login_required
def view_arguments(request):
    return render(request, 'ethics/view_arguments.html')
