"""
Config Module Tests
"""
import pytest
import os
from src.infrastructure.config import Config, Environment


class TestConfig:
    """Config 클래스 테스트"""

    def test_create_config(self):
        config = Config(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678-01",
            environment=Environment.DEVELOPMENT,
        )

        assert config.app_key == "test_key"
        assert config.app_secret == "test_secret"
        assert config.account_no == "12345678-01"
        assert config.environment == Environment.DEVELOPMENT

    def test_base_url_development(self):
        config = Config(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678-01",
            environment=Environment.DEVELOPMENT,
        )

        assert "openapivts" in config.base_url

    def test_base_url_production(self):
        config = Config(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678-01",
            environment=Environment.PRODUCTION,
        )

        assert "openapivts" not in config.base_url
        assert "openapi.koreainvestment" in config.base_url

    def test_account_prefix(self):
        config = Config(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678-01",
            environment=Environment.DEVELOPMENT,
        )

        assert config.account_prefix == "12345678"

    def test_account_suffix(self):
        config = Config(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678-01",
            environment=Environment.DEVELOPMENT,
        )

        assert config.account_suffix == "01"

    def test_get_tr_id_development(self):
        config = Config(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678-01",
            environment=Environment.DEVELOPMENT,
        )

        assert config.get_tr_id("buy") == "VTTC0802U"
        assert config.get_tr_id("sell") == "VTTC0801U"

    def test_get_tr_id_production(self):
        config = Config(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678-01",
            environment=Environment.PRODUCTION,
        )

        assert config.get_tr_id("buy") == "TTTC0802U"
        assert config.get_tr_id("sell") == "TTTC0801U"

    def test_create_method(self):
        config = Config.create(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678-01",
            is_production=True,
        )

        assert config.environment == Environment.PRODUCTION

    def test_create_method_development(self):
        config = Config.create(
            app_key="test_key",
            app_secret="test_secret",
            account_no="12345678-01",
            is_production=False,
        )

        assert config.environment == Environment.DEVELOPMENT


class TestEnvironment:
    """Environment 열거형 테스트"""

    def test_environment_values(self):
        assert Environment.PRODUCTION.value == "prod"
        assert Environment.DEVELOPMENT.value == "dev"
