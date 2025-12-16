"""
Test Fixtures - 테스트용 공통 픽스처
"""
import pytest
from typing import Dict, Any, Optional
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.domain.interfaces import IHttpClient, IAuthProvider
from src.infrastructure.config import Config, Environment


class MockHttpClient(IHttpClient):
    """테스트용 Mock HTTP 클라이언트"""

    def __init__(self):
        self.get_response: Dict[str, Any] = {}
        self.post_response: Dict[str, Any] = {}
        self.get_calls = []
        self.post_calls = []

    def get(
        self,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.get_calls.append({"url": url, "headers": headers, "params": params})
        return self.get_response

    def post(
        self,
        url: str,
        headers: Dict[str, str],
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self.post_calls.append({"url": url, "headers": headers, "data": data})
        return self.post_response

    def set_get_response(self, response: Dict[str, Any]):
        self.get_response = response

    def set_post_response(self, response: Dict[str, Any]):
        self.post_response = response


class MockAuthProvider(IAuthProvider):
    """테스트용 Mock 인증 제공자"""

    def __init__(self):
        self._token = "test_token"
        self._authenticated = True

    def get_access_token(self) -> Optional[str]:
        return self._token

    def get_headers(self) -> Dict[str, str]:
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self._token}",
            "appkey": "test_app_key",
            "appsecret": "test_app_secret",
        }

    def is_authenticated(self) -> bool:
        return self._authenticated


@pytest.fixture
def mock_config() -> Config:
    """테스트용 설정"""
    return Config(
        app_key="test_app_key",
        app_secret="test_app_secret",
        account_no="12345678-01",
        environment=Environment.DEVELOPMENT,
    )


@pytest.fixture
def mock_http_client() -> MockHttpClient:
    """테스트용 HTTP 클라이언트"""
    return MockHttpClient()


@pytest.fixture
def mock_auth_provider() -> MockAuthProvider:
    """테스트용 인증 제공자"""
    return MockAuthProvider()
