"""
Keycloak OIDC backend для Django
"""
import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class KeycloakBackend(ModelBackend):
    """Authentication backend для Keycloak"""

    def authenticate(self, request, access_token=None, **kwargs):
        if not access_token:
            return None

        try:
            # Получить userinfo из Keycloak
            userinfo_url = request.session.get("oidc_op_user_endpoint")
            if not userinfo_url:
                return None

            response = requests.get(
                userinfo_url,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            response.raise_for_status()
            userinfo = response.json()

            # Получить или создать пользователя
            username = userinfo.get("preferred_username") or userinfo.get("email")
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={
                    "email": userinfo.get("email", ""),
                    "first_name": userinfo.get("given_name", ""),
                    "last_name": userinfo.get("family_name", ""),
                },
            )

            # Сохранить информацию в сессию
            if request:
                request.session["oidc_access_token"] = access_token
                request.session["oidc_userinfo"] = userinfo

            return user
        except Exception:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None