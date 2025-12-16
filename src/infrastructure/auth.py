"""
Authentication Module - 인증 처리 담당 (SRP 준수)
"""
from typing import Dict, Optional

from ..domain.interfaces import IAuthProvider, IHttpClient
from .config import Config


class AuthenticationError(Exception):
    """인증 에러"""
    pass


class KISAuthProvider(IAuthProvider):
    """한국투자증권 인증 제공자"""

    TOKEN_ENDPOINT = "/oauth2/tokenP"

    def __init__(self, config: Config, http_client: IHttpClient):
        self._config = config
        self._http_client = http_client
        self._access_token: Optional[str] = None
        self._token_type: str = "Bearer"

    def get_access_token(self) -> Optional[str]:
        """OAuth 액세스 토큰 발급"""
        url = f"{self._config.base_url}{self.TOKEN_ENDPOINT}"

        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self._config.app_key,
            "appsecret": self._config.app_secret,
        }

        try:
            response = self._http_client.post(url, headers=headers, data=body)

            if "access_token" in response:
                self._access_token = response["access_token"]
                self._token_type = response.get("token_type", "Bearer")
                return self._access_token
            else:
                error_msg = response.get("error_description", "Unknown error")
                raise AuthenticationError(f"Token issuance failed: {error_msg}")

        except Exception as e:
            raise AuthenticationError(f"Authentication failed: {str(e)}")

    def get_headers(self) -> Dict[str, str]:
        """API 호출용 인증 헤더 반환"""
        if not self._access_token:
            self.get_access_token()

        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"{self._token_type} {self._access_token}",
            "appkey": self._config.app_key,
            "appsecret": self._config.app_secret,
        }

    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        return self._access_token is not None

    def clear_token(self) -> None:
        """토큰 초기화"""
        self._access_token = None
