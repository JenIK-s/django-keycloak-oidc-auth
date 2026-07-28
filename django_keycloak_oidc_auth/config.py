from django.conf import settings

OIDC_RP_CLIENT_ID = settings.DKA_CLIENT_ID
OIDC_RP_CLIENT_SECRET = settings.DKA_CLIENT_SECRET
OIDC_VERIFY_SSL = getattr(settings, "DKA_VERIFY_SSL", True)

KC_BASE_URL = f"https://{settings.DKA_BASE_URL}/realms/{settings.DKA_REALM}/protocol/openid-connect"

OIDC_OP_AUTHORIZATION_ENDPOINT = f"{KC_BASE_URL}/auth"
OIDC_OP_TOKEN_ENDPOINT = f"{KC_BASE_URL}/token"
OIDC_OP_USER_ENDPOINT = f"{KC_BASE_URL}/userinfo"
OIDC_OP_JWKS_ENDPOINT = f"{KC_BASE_URL}/certs"
OIDC_OP_LOGOUT_ENDPOINT = f"{KC_BASE_URL}/logout"
