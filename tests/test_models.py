"""
Domain Models Tests
"""
import pytest
from src.domain.models import (
    StockPrice,
    AskingPrice,
    DailyPrice,
    Holdings,
    AccountSummary,
    Balance,
    Deposit,
    OrderResult,
    OrderInfo,
    OrderType,
    OrderSide,
)


class TestStockPrice:
    """StockPrice 모델 테스트"""

    def test_create_stock_price(self):
        price = StockPrice(
            stock_code="005930",
            current_price=70000,
            change_price=-1000,
            change_rate=-1.41,
            open_price=71000,
            high_price=71500,
            low_price=69500,
            volume=10000000,
        )

        assert price.stock_code == "005930"
        assert price.current_price == 70000
        assert price.change_price == -1000
        assert price.change_rate == -1.41

    def test_to_dict(self):
        price = StockPrice(
            stock_code="005930",
            current_price=70000,
            change_price=-1000,
            change_rate=-1.41,
            open_price=71000,
            high_price=71500,
            low_price=69500,
            volume=10000000,
        )

        result = price.to_dict()
        assert result["종목코드"] == "005930"
        assert result["현재가"] == 70000
        assert result["전일대비"] == -1000


class TestAskingPrice:
    """AskingPrice 모델 테스트"""

    def test_create_asking_price(self):
        asking = AskingPrice(
            sell_prices=[70100, 70200, 70300],
            buy_prices=[70000, 69900, 69800],
            sell_volumes=[1000, 2000, 3000],
            buy_volumes=[1500, 2500, 3500],
        )

        assert asking.sell_prices[0] == 70100
        assert asking.buy_prices[0] == 70000

    def test_to_dict(self):
        asking = AskingPrice(
            sell_prices=[70100, 70200, 70300],
            buy_prices=[70000, 69900, 69800],
            sell_volumes=[1000, 2000, 3000],
            buy_volumes=[1500, 2500, 3500],
        )

        result = asking.to_dict()
        assert result["매도호가1"] == 70100
        assert result["매수호가1"] == 70000
        assert result["매도잔량1"] == 1000


class TestDailyPrice:
    """DailyPrice 모델 테스트"""

    def test_create_daily_price(self):
        daily = DailyPrice(
            date="20251216",
            close_price=70000,
            open_price=71000,
            high_price=71500,
            low_price=69500,
            volume=10000000,
        )

        assert daily.date == "20251216"
        assert daily.close_price == 70000


class TestHoldings:
    """Holdings 모델 테스트"""

    def test_create_holdings(self):
        holding = Holdings(
            stock_code="005930",
            stock_name="삼성전자",
            quantity=10,
            avg_buy_price=68000,
            current_price=70000,
            eval_amount=700000,
            profit_loss=20000,
            profit_rate=2.94,
        )

        assert holding.stock_code == "005930"
        assert holding.quantity == 10
        assert holding.profit_rate == 2.94


class TestOrderInfo:
    """OrderInfo 모델 테스트"""

    def test_is_executed_true(self):
        order = OrderInfo(
            order_no="0001",
            stock_code="005930",
            stock_name="삼성전자",
            order_side="매수",
            order_qty=10,
            order_price=70000,
            executed_qty=10,
            executed_price=70000,
            order_time="100000",
        )

        assert order.is_executed is True
        assert order.status == "체결완료"

    def test_is_executed_false(self):
        order = OrderInfo(
            order_no="0001",
            stock_code="005930",
            stock_name="삼성전자",
            order_side="매수",
            order_qty=10,
            order_price=70000,
            executed_qty=5,
            executed_price=70000,
            order_time="100000",
        )

        assert order.is_executed is False
        assert order.status == "미체결(5/10)"


class TestOrderType:
    """OrderType 열거형 테스트"""

    def test_order_type_values(self):
        assert OrderType.LIMIT.value == "00"
        assert OrderType.MARKET.value == "01"


class TestOrderSide:
    """OrderSide 열거형 테스트"""

    def test_order_side_values(self):
        assert OrderSide.BUY.value == "buy"
        assert OrderSide.SELL.value == "sell"
