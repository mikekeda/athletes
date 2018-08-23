from django.urls import path

from .views import home_page, about_page, login_page, logout_page


app_name = "Athletes"

urlpatterns = [
    path('', home_page, name='home'),
    path('about', about_page, name='about'),
    path('login', login_page, name='login'),
    path('logout', logout_page, name='logout'),
]
