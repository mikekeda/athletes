from django.urls import path
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, \
    TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from api.viewsets import AthleteViewSet, TeamViewSet

app_name = "Api"


class ApiTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data['username'] = self.user.username

        return data


class ApiTokenObtainPairView(TokenObtainPairView):
    """
    Takes a set of user credentials and returns username and an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """
    serializer_class = ApiTokenObtainPairSerializer

    def options(self, request, *args, **kwargs):
        response = super().options(request, *args, **kwargs)

        response['Access-Control-Allow-Origin'] = '*'

        return response

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        response['Access-Control-Allow-Origin'] = '*'

        return response


urlpatterns = [
    path('token', ApiTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
]


# Routers provide a way of automatically determining the URL conf.
router = routers.DefaultRouter()
router.register(r'athletes', AthleteViewSet)
router.register(r'teams', TeamViewSet)
