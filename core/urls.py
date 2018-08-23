from django.urls import path

from .views import home_page, about_page


app_name = "Athletes"

urlpatterns = [
    path('', home_page, name='home'),
    path('about', about_page, name='about'),
]
