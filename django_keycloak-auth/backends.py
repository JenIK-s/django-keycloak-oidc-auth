"""
Keycloak OIDC backend для Django
"""
from __future__ import annotations

from typing import Any

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.base_user import AbstractBaseUser
from django.http import HttpRequest

from .config import OIDC_OP_USER_ENDPOINT

User = get_user_model()


class KeycloakBackend(ModelBackend):
    """Authentication backend для Keycloak."""

    UserModel = User

    def filter_users_by_claims(self, claims: dict[str, Any]):
        """Возвращает queryset пользователей с email из OIDC claims."""
        email = claims.get("email")
        if not email:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(email__iexact=email)

    def create_user(self, claims: dict[str, Any]) -> AbstractBaseUser:
        """Создаёт пользователя без пароля; для заданного email — staff/superuser."""
        email = claims.get("email")
        if not email:
            raise ValueError("email claim is required")

        username = email.split("@")[0]
        super_user_email = getattr(settings, "DKA_SUPER_USER_EMAIL", None)

        if super_user_email and super_user_email.lower() == email.lower():
            user = self.UserModel.objects.create_user(
                username=username,
                email=email,
                is_superuser=True,
                is_staff=True,
            )
        else:
            user = self.UserModel.objects.create_user(
                username=username,
                email=email,
            )
        user.set_unusable_password()
        user.save()
        return user

    def authenticate(
        self,
        request: HttpRequest | None = None,
        access_token: str | None = None,
        **kwargs: Any,
    ) -> AbstractBaseUser | None:
        """Авторизует пользователя по access_token от Keycloak."""
        if not access_token:
            return None

        try:
            response = requests.get(
                OIDC_OP_USER_ENDPOINT,
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            response.raise_for_status()
            claims = response.json()
        except Exception:
            return None

        users = self.filter_users_by_claims(claims)
        user = users.first()
        if user is None:
            user = self.create_user(claims)

        return user if self.user_can_authenticate(user) else None
