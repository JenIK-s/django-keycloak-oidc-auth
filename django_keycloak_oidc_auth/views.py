"""
Keycloak OIDC views для логина/логаута.
"""
import uuid
from urllib.parse import urlencode

import requests
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import View

from .config import (
    OIDC_OP_AUTHORIZATION_ENDPOINT,
    OIDC_OP_TOKEN_ENDPOINT,
    OIDC_RP_CLIENT_ID,
    OIDC_RP_CLIENT_SECRET,
    OIDC_VERIFY_SSL,
)


def build_callback_uri(request) -> str:
    return request.build_absolute_uri(reverse("django_keycloak_oidc_auth:callback"))


class KeycloakLoginView(View):
    """Начать процесс логина"""

    def get(self, request):
        state = str(uuid.uuid4())
        request.session["oidc_state"] = state
        next_url = request.GET.get("next") or "/"
        request.session["login_next"] = next_url

        redirect_uri = build_callback_uri(request)
        auth_url = f"{OIDC_OP_AUTHORIZATION_ENDPOINT}?{urlencode({
            'client_id': OIDC_RP_CLIENT_ID,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': 'openid profile email',
            'state': state,
        })}"

        return HttpResponseRedirect(auth_url)


class KeycloakCallbackView(View):
    """Обработать callback от Keycloak"""

    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")

        if not code or state != request.session.get("oidc_state"):
            return HttpResponse("Invalid callback", status=400)

        try:
            # Обменять код на токен
            redirect_uri = build_callback_uri(request)
            token_response = requests.post(
                OIDC_OP_TOKEN_ENDPOINT,
                data={
                    "grant_type": "authorization_code",
                    "client_id": OIDC_RP_CLIENT_ID,
                    "client_secret": OIDC_RP_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                timeout=10,
                verify=OIDC_VERIFY_SSL,
            )
            token_response.raise_for_status()
            tokens = token_response.json()

            # Авторизовать пользователя
            user = authenticate(
                request,
                access_token=tokens["access_token"],
            )

            if user:
                login(
                    request,
                    user,
                    backend="django_keycloak_oidc_auth.backends.KeycloakBackend",
                )
                request.session["oidc_refresh_token"] = tokens.get("refresh_token")
                request.session.pop("oidc_state", None)
                next_url = request.session.pop("login_next", "/")
                return HttpResponseRedirect(next_url)

            return HttpResponse("Authentication failed", status=401)

        except Exception as e:
            return HttpResponse(f"Error: {e}", status=500)


class KeycloakLogoutView(View):
    """Выход из приложения"""

    def get(self, request):
        logout(request)
        return HttpResponseRedirect("/")

    def post(self, request):
        return self.get(request)
