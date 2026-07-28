from django.urls import path

from .views import KeycloakCallbackView, KeycloakLoginView, KeycloakLogoutView

app_name = "django_keycloak_oidc_auth"

urlpatterns = [
    path("login/", KeycloakLoginView.as_view(), name="login"),
    path("callback/", KeycloakCallbackView.as_view(), name="callback"),
    path("logout/", KeycloakLogoutView.as_view(), name="logout"),
]
