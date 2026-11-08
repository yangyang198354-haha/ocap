"""令牌认证（IFC-038）。"""
from rest_framework.authentication import BaseAuthentication, get_authorization_header

from .services import AccountService


class TokenAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header:
            return None
        if len(header) != 2 or header[0].lower() != self.keyword.lower().encode():
            return None
        key = header[1].decode("utf-8", errors="ignore")
        principal = AccountService.authenticate_token(key)
        return principal, key

    def authenticate_header(self, request):
        return "Bearer"
