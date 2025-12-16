"""
Account Service Tests
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.application.account_service import KISAccountService
from src.infrastructure.config import Config, Environment


class TestKISAccountService:
    """계좌 서비스 테스트"""

    @pytest.fixture
    def account_service(self, mock_config, mock_http_client, mock_auth_provider):
        return KISAccountService(
            config=mock_config,
            auth_provider=mock_auth_provider,
            http_client=mock_http_client,
        )

    def test_get_balance_success(self, account_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "0",
            "output1": [
                {
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "hldg_qty": "10",
                    "pchs_avg_pric": "68000",
                    "prpr": "70000",
                    "evlu_amt": "700000",
                    "evlu_pfls_amt": "20000",
                    "evlu_pfls_rt": "2.94",
                },
            ],
            "output2": [
                {
                    "dnca_tot_amt": "1000000",
                    "pchs_amt_smtl_amt": "680000",
                    "evlu_amt_smtl_amt": "700000",
                    "evlu_pfls_smtl_amt": "20000",
                },
            ],
        })

        # When
        result = account_service.get_balance()

        # Then
        assert result is not None
        assert len(result.holdings) == 1
        assert result.holdings[0].stock_code == "005930"
        assert result.holdings[0].quantity == 10
        assert result.summary.deposit == 1000000

    def test_get_balance_empty_holdings(self, account_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "0",
            "output1": [
                {
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "hldg_qty": "0",  # 보유수량 0
                    "pchs_avg_pric": "0",
                    "prpr": "70000",
                    "evlu_amt": "0",
                    "evlu_pfls_amt": "0",
                    "evlu_pfls_rt": "0",
                },
            ],
            "output2": [
                {
                    "dnca_tot_amt": "1000000",
                    "pchs_amt_smtl_amt": "0",
                    "evlu_amt_smtl_amt": "0",
                    "evlu_pfls_smtl_amt": "0",
                },
            ],
        })

        # When
        result = account_service.get_balance()

        # Then
        assert result is not None
        assert len(result.holdings) == 0

    def test_get_balance_failure(self, account_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "1",
            "msg1": "조회 실패",
        })

        # When
        result = account_service.get_balance()

        # Then
        assert result is None

    def test_get_available_deposit_success(self, account_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "0",
            "output": {
                "ord_psbl_cash": "500000",
                "nrcvb_buy_amt": "480000",
            },
        })

        # When
        result = account_service.get_available_deposit()

        # Then
        assert result is not None
        assert result.available_cash == 500000
        assert result.available_total == 480000

    def test_get_available_deposit_failure(self, account_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "1",
            "msg1": "조회 실패",
        })

        # When
        result = account_service.get_available_deposit()

        # Then
        assert result is None
