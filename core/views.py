from django.conf import settings
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.http import JsonResponse
from django.shortcuts import render, redirect, reverse


@login_required
def athletes_api(request):
    """ Home page. """
    return JsonResponse([
        {
            "Column 1": "Row 1 Data 1",
            "Column 2": "Row 1 Data 2",
        },
        {
            "Column 1": "Row 2 Data 1",
            "Column 2": "Row 2 Data 2",
        },
        {
            "Column 1": "Row 3 Data 1",
            "Column 2": "Row 3 Data 2",
        },
    ], safe=False)


@login_required
def home_page(request):
    """ Home page. """
    return render(request, 'home.html')


def about_page(request):
    """ About page. """
    return render(request, 'about.html')


def login_page(request):
    """ User login page. """
    if request.user.is_authenticated:
        return redirect(settings.LOGIN_REDIRECT_URL)
    form = AuthenticationForm()
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(reverse('core:crm'))

    return render(request, 'login.html', {'form': form})


@login_required
def logout_page(request):
    """ User logout callback. """
    logout(request)
    return redirect(reverse('core:login'))
