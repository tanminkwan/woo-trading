"""
HTTP Client Module - HTTP 통신 담당 (SRP 준수)
"""
import requests
from typing import Dict, Any, Optional
import urllib3

from ..domain.interfaces import IHttpClient

# SSL 경고 비활성화 (모의투자 서버용)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class HttpClientError(Exception):
    """HTTP 클라이언트 에러"""
    def __init__(self, status_code: int, message: str, response_body: str = ""):
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"HTTP {status_code}: {message}")


class RequestsHttpClient(IHttpClient):
    """requests 라이브러리 기반 HTTP 클라이언트"""

    def __init__(self, timeout: int = 30, verify_ssl: bool = False):
        self._timeout = timeout
        self._verify_ssl = verify_ssl

    def get(
        self,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """GET 요청"""
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=self._timeout,
            verify=self._verify_ssl,
        )

        return self._handle_response(response)

    def post(
        self,
        url: str,
        headers: Dict[str, str],
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """POST 요청"""
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=self._timeout,
            verify=self._verify_ssl,
        )

        return self._handle_response(response)

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """응답 처리"""
        if response.status_code != 200:
            raise HttpClientError(
                status_code=response.status_code,
                message=f"Request failed",
                response_body=response.text,
            )

        return response.json()
