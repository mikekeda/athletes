from django.urls import path

from .views import home_page, about_page, login_page, logout_page


app_name = "Athletes"

urlpatterns = [
    path('', about_page, name='home'),
    path('crm', home_page, name='crm'),
    path('login', login_page, name='login'),
    path('logout', logout_page, name='logout'),
]
