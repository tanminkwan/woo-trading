"""
Order Service Tests
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.application.order_service import KISOrderService
from src.domain.models import OrderType
from src.infrastructure.config import Config, Environment


class TestKISOrderService:
    """주문 서비스 테스트"""

    @pytest.fixture
    def order_service(self, mock_config, mock_http_client, mock_auth_provider):
        return KISOrderService(
            config=mock_config,
            auth_provider=mock_auth_provider,
            http_client=mock_http_client,
        )

    def test_buy_success(self, order_service, mock_http_client):
        # Given
        mock_http_client.set_post_response({
            "rt_cd": "0",
            "msg1": "주문 성공",
            "output": {
                "ODNO": "0012345678",
                "ORD_TMD": "100000",
            },
        })

        # When
        result = order_service.buy("005930", quantity=10, price=70000)

        # Then
        assert result.success is True
        assert result.order_no == "0012345678"
        assert result.order_time == "100000"

    def test_buy_failure(self, order_service, mock_http_client):
        # Given
        mock_http_client.set_post_response({
            "rt_cd": "1",
            "msg1": "주문 실패: 잔액 부족",
        })

        # When
        result = order_service.buy("005930", quantity=10, price=70000)

        # Then
        assert result.success is False
        assert "주문 실패" in result.message

    def test_sell_success(self, order_service, mock_http_client):
        # Given
        mock_http_client.set_post_response({
            "rt_cd": "0",
            "msg1": "주문 성공",
            "output": {
                "ODNO": "0012345679",
                "ORD_TMD": "100100",
            },
        })

        # When
        result = order_service.sell("005930", quantity=5, price=71000)

        # Then
        assert result.success is True
        assert result.order_no == "0012345679"

    def test_buy_market_order(self, order_service, mock_http_client):
        # Given
        mock_http_client.set_post_response({
            "rt_cd": "0",
            "msg1": "주문 성공",
            "output": {
                "ODNO": "0012345680",
                "ORD_TMD": "100200",
            },
        })

        # When
        result = order_service.buy("005930", quantity=10, price=0)  # 시장가

        # Then
        assert result.success is True
        # Verify market order was sent
        call = mock_http_client.post_calls[0]
        assert call["data"]["ORD_DVSN"] == "01"  # 시장가

    def test_buy_limit_order(self, order_service, mock_http_client):
        # Given
        mock_http_client.set_post_response({
            "rt_cd": "0",
            "msg1": "주문 성공",
            "output": {
                "ODNO": "0012345681",
                "ORD_TMD": "100300",
            },
        })

        # When
        result = order_service.buy("005930", quantity=10, price=70000)  # 지정가

        # Then
        assert result.success is True
        # Verify limit order was sent
        call = mock_http_client.post_calls[0]
        assert call["data"]["ORD_DVSN"] == "00"  # 지정가
        assert call["data"]["ORD_UNPR"] == "70000"

    def test_get_orders_success(self, order_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "0",
            "output1": [
                {
                    "odno": "0012345678",
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "sll_buy_dvsn_cd": "02",  # 매수
                    "ord_qty": "10",
                    "ord_unpr": "70000",
                    "tot_ccld_qty": "10",
                    "avg_prvs": "70000",
                    "ord_tmd": "100000",
                },
                {
                    "odno": "0012345679",
                    "pdno": "005930",
                    "prdt_name": "삼성전자",
                    "sll_buy_dvsn_cd": "01",  # 매도
                    "ord_qty": "5",
                    "ord_unpr": "71000",
                    "tot_ccld_qty": "0",
                    "avg_prvs": "0",
                    "ord_tmd": "100100",
                },
            ],
        })

        # When
        result = order_service.get_orders()

        # Then
        assert result is not None
        assert len(result) == 2
        assert result[0].order_no == "0012345678"
        assert result[0].order_side == "매수"
        assert result[0].is_executed is True
        assert result[1].order_side == "매도"
        assert result[1].is_executed is False

    def test_get_orders_empty(self, order_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "0",
            "output1": [],
        })

        # When
        result = order_service.get_orders()

        # Then
        assert result is not None
        assert len(result) == 0

    def test_get_orders_failure(self, order_service, mock_http_client):
        # Given
        mock_http_client.set_get_response({
            "rt_cd": "1",
            "msg1": "조회 실패",
        })

        # When
        result = order_service.get_orders()

        # Then
        assert result is None
