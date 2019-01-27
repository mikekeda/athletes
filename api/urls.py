from django.urls import path
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, \
    TokenRefreshView

from api.viewsets import AthleteViewSet, TeamViewSet

app_name = "Api"

urlpatterns = [
    path('token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
]


# Routers provide a way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'athletes', AthleteViewSet)
router.register(r'teams', TeamViewSet)
