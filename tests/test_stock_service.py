"""
Stock Service Tests
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.application.stock_service import KISStockService
from src.infrastructure.config import Config, Environment


class TestKISStockService:
    """주식 시세 서비스 테스트"""

    @pytest.fixture
    def stock_service(self, mock_config, mock_http_client, mock_auth_provider):
        return KISStockService(
            config=mock_config,
            auth_provider=mock_auth_provider,
            http_client=mock_http_client,
        )

    def test_get_price_success(self, stock_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "0",
            "output": {
                "stck_prpr": "70000",
                "prdy_vrss": "-1000",
                "prdy_ctrt": "-1.41",
                "stck_oprc": "71000",
                "stck_hgpr": "71500",
                "stck_lwpr": "69500",
                "acml_vol": "10000000",
            },
        })

        # When
        result = stock_service.get_price("005930")

        # Then
        assert result is not None
        assert result.stock_code == "005930"
        assert result.current_price == 70000
        assert result.change_price == -1000
        assert result.change_rate == -1.41

    def test_get_price_failure(self, stock_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "1",
            "msg1": "조회 실패",
        })

        # When
        result = stock_service.get_price("005930")

        # Then
        assert result is None

    def test_get_asking_price_success(self, stock_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "0",
            "output1": {
                "askp1": "70100",
                "askp2": "70200",
                "askp3": "70300",
                "bidp1": "70000",
                "bidp2": "69900",
                "bidp3": "69800",
                "askp_rsqn1": "1000",
                "askp_rsqn2": "2000",
                "askp_rsqn3": "3000",
                "bidp_rsqn1": "1500",
                "bidp_rsqn2": "2500",
                "bidp_rsqn3": "3500",
            },
        })

        # When
        result = stock_service.get_asking_price("005930")

        # Then
        assert result is not None
        assert result.sell_prices[0] == 70100
        assert result.buy_prices[0] == 70000
        assert result.sell_volumes[0] == 1000

    def test_get_daily_prices_success(self, stock_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "0",
            "output": [
                {
                    "stck_bsop_date": "20251216",
                    "stck_clpr": "70000",
                    "stck_oprc": "71000",
                    "stck_hgpr": "71500",
                    "stck_lwpr": "69500",
                    "acml_vol": "10000000",
                },
                {
                    "stck_bsop_date": "20251215",
                    "stck_clpr": "71000",
                    "stck_oprc": "70500",
                    "stck_hgpr": "71500",
                    "stck_lwpr": "70000",
                    "acml_vol": "8000000",
                },
            ],
        })

        # When
        result = stock_service.get_daily_prices("005930")

        # Then
        assert result is not None
        assert len(result) == 2
        assert result[0].date == "20251216"
        assert result[0].close_price == 70000

    def test_api_call_includes_correct_headers(self, stock_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "0",
            "output": {
                "stck_prpr": "70000",
                "prdy_vrss": "-1000",
                "prdy_ctrt": "-1.41",
                "stck_oprc": "71000",
                "stck_hgpr": "71500",
                "stck_lwpr": "69500",
                "acml_vol": "10000000",
            },
        })

        # When
        stock_service.get_price("005930")

        # Then
        assert len(mock_http_client.get_calls) == 1
        call = mock_http_client.get_calls[0]
        assert "tr_id" in call["headers"]
        assert call["params"]["FID_INPUT_ISCD"] == "005930"
