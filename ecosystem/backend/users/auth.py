from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class ActiveTokenAuthentication(TokenAuthentication):
    """Suspended accounts are turned away even if they still hold a token."""

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)
        if user.is_suspended:
            raise AuthenticationFailed("This account is suspended. Ask the owner.")
        return user, token
