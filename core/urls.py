from django.urls import path

from .views import (crm_page, about_page, login_page, logout_page,
                    athletes_api, ParseTeamView)


app_name = "Athletes"

urlpatterns = [
    path('', about_page, name='home'),
    path('crm', crm_page, name='crm'),
    path('team', ParseTeamView.as_view(), name='team'),
    path('api/athletes', athletes_api, name='athletes-api'),
    path('login', login_page, name='login'),
    path('logout', logout_page, name='logout'),
]
