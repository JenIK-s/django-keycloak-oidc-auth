"""
Keycloak OIDC views для логина/логаута
"""
import uuid
import requests
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.views import View
from .config import *


class KeycloakLoginView(View):
    """Начать процесс логина"""

    def get(self, request):
        state = str(uuid.uuid4())
        request.session["oidc_state"] = state
        next_url = request.GET.get("next") or "/"
        request.session["login_next"] = next_url

        redirect_uri = request.build_absolute_uri("/oidc/callback/")
        auth_url = (
            f"{OIDC_OP_AUTHORIZATION_ENDPOINT}?"
            f"client_id={OIDC_RP_CLIENT_ID}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"scope=openid+profile+email&"
            f"state={state}"
        )

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
            redirect_uri = request.build_absolute_uri("/oidc/callback/")
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
            )
            token_response.raise_for_status()
            tokens = token_response.json()

            # Авторизовать пользователя
            user = authenticate(
                request,
                access_token=tokens["access_token"],
            )

            if user:
                login(request, user, backend="django_keycloak.backends.KeycloakBackend")
                request.session["oidc_refresh_token"] = tokens.get("refresh_token")
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
