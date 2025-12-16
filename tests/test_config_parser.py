"""
Config Parser Tests
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.engine.config_parser import TradingConfig, StockConfig


class TestStockConfig:
    """StockConfig 테스트"""

    def test_create_stock_config(self):
        config = StockConfig(
            code="005930",
            name="삼성전자",
            max_amount=1000000,
            buy_price=50000,
            sell_price=60000,
            interval=30,
            enabled=True,
        )

        assert config.code == "005930"
        assert config.name == "삼성전자"
        assert config.max_amount == 1000000
        assert config.buy_price == 50000
        assert config.sell_price == 60000
        assert config.interval == 30
        assert config.enabled is True

    def test_to_dict(self):
        config = StockConfig(
            code="005930",
            name="삼성전자",
            max_amount=1000000,
            buy_price=50000,
            sell_price=60000,
        )

        result = config.to_dict()
        assert result["code"] == "005930"
        assert result["name"] == "삼성전자"
        assert result["max_amount"] == 1000000

    def test_from_dict(self):
        data = {
            "code": "005930",
            "name": "삼성전자",
            "max_amount": 1000000,
            "buy_price": 50000,
            "sell_price": 60000,
            "enabled": True,
        }

        config = StockConfig.from_dict(data)
        assert config.code == "005930"
        assert config.max_amount == 1000000


class TestTradingConfig:
    """TradingConfig 테스트"""

    def test_create_trading_config(self):
        config = TradingConfig(
            default_interval=60,
            max_daily_trades=10,
            stocks=[],
        )

        assert config.default_interval == 60
        assert config.max_daily_trades == 10
        assert len(config.stocks) == 0

    def test_get_enabled_stocks(self):
        config = TradingConfig(
            stocks=[
                StockConfig("005930", "삼성전자", 1000000, 50000, 60000, enabled=True),
                StockConfig("000660", "SK하이닉스", 500000, 170000, 200000, enabled=False),
            ]
        )

        enabled = config.get_enabled_stocks()
        assert len(enabled) == 1
        assert enabled[0].code == "005930"

    def test_get_stock_by_code(self):
        config = TradingConfig(
            stocks=[
                StockConfig("005930", "삼성전자", 1000000, 50000, 60000),
            ]
        )

        stock = config.get_stock_by_code("005930")
        assert stock is not None
        assert stock.name == "삼성전자"

        not_found = config.get_stock_by_code("999999")
        assert not_found is None

    def test_get_interval_with_stock_interval(self):
        config = TradingConfig(default_interval=60)
        stock = StockConfig("005930", "삼성전자", 1000000, 50000, 60000, interval=30)

        interval = config.get_interval(stock)
        assert interval == 30

    def test_get_interval_without_stock_interval(self):
        config = TradingConfig(default_interval=60)
        stock = StockConfig("005930", "삼성전자", 1000000, 50000, 60000, interval=None)

        interval = config.get_interval(stock)
        assert interval == 60

    def test_add_stock(self):
        config = TradingConfig()
        stock = StockConfig("005930", "삼성전자", 1000000, 50000, 60000)

        config.add_stock(stock)
        assert len(config.stocks) == 1
        assert config.stocks[0].code == "005930"

    def test_add_stock_update_existing(self):
        config = TradingConfig(
            stocks=[
                StockConfig("005930", "삼성전자", 1000000, 50000, 60000),
            ]
        )

        new_stock = StockConfig("005930", "삼성전자", 2000000, 55000, 65000)
        config.add_stock(new_stock)

        assert len(config.stocks) == 1
        assert config.stocks[0].max_amount == 2000000

    def test_remove_stock(self):
        config = TradingConfig(
            stocks=[
                StockConfig("005930", "삼성전자", 1000000, 50000, 60000),
            ]
        )

        result = config.remove_stock("005930")
        assert result is True
        assert len(config.stocks) == 0

    def test_remove_stock_not_found(self):
        config = TradingConfig()

        result = config.remove_stock("999999")
        assert result is False

    def test_to_yaml_and_from_yaml(self):
        original = TradingConfig(
            default_interval=60,
            max_daily_trades=10,
            stocks=[
                StockConfig("005930", "삼성전자", 1000000, 50000, 60000),
            ]
        )

        yaml_str = original.to_yaml()
        loaded = TradingConfig.from_yaml(yaml_str)

        assert loaded.default_interval == 60
        assert loaded.max_daily_trades == 10
        assert len(loaded.stocks) == 1
        assert loaded.stocks[0].code == "005930"

    def test_update_stock_enabled(self):
        config = TradingConfig(
            stocks=[
                StockConfig("005930", "삼성전자", 1000000, 50000, 60000, enabled=True),
            ]
        )

        result = config.update_stock_enabled("005930", False)
        assert result is True

        stock = config.get_stock_by_code("005930")
        assert stock.enabled is False

    def test_priority_default_value(self):
        """우선순위 기본값 테스트"""
        config = StockConfig("005930", "삼성전자", 1000000, 50000, 60000)
        assert config.priority == 100

    def test_priority_custom_value(self):
        """우선순위 커스텀 값 테스트"""
        config = StockConfig("005930", "삼성전자", 1000000, 50000, 60000, priority=1)
        assert config.priority == 1

    def test_priority_from_dict(self):
        """딕셔너리에서 우선순위 로드 테스트"""
        data = {
            "code": "005930",
            "name": "삼성전자",
            "max_amount": 1000000,
            "buy_price": 50000,
            "sell_price": 60000,
            "priority": 5,
        }
        config = StockConfig.from_dict(data)
        assert config.priority == 5

    def test_priority_to_dict(self):
        """딕셔너리로 우선순위 내보내기 테스트"""
        config = StockConfig("005930", "삼성전자", 1000000, 50000, 60000, priority=3)
        result = config.to_dict()
        assert result["priority"] == 3

    def test_get_enabled_stocks_sorted_by_priority(self):
        """활성화된 종목이 우선순위 순으로 정렬되는지 테스트"""
        config = TradingConfig(
            stocks=[
                StockConfig("005930", "삼성전자", 1000000, 50000, 60000, enabled=True, priority=3),
                StockConfig("000660", "SK하이닉스", 500000, 170000, 200000, enabled=True, priority=1),
                StockConfig("035420", "NAVER", 800000, 180000, 220000, enabled=True, priority=2),
            ]
        )

        enabled = config.get_enabled_stocks()
        assert len(enabled) == 3
        assert enabled[0].code == "000660"  # priority 1
        assert enabled[1].code == "035420"  # priority 2
        assert enabled[2].code == "005930"  # priority 3

    def test_update_stock_priority(self):
        """종목 우선순위 변경 테스트"""
        config = TradingConfig(
            stocks=[
                StockConfig("005930", "삼성전자", 1000000, 50000, 60000, priority=100),
            ]
        )

        result = config.update_stock_priority("005930", 1)
        assert result is True

        stock = config.get_stock_by_code("005930")
        assert stock.priority == 1

    def test_update_stock_priority_not_found(self):
        """존재하지 않는 종목 우선순위 변경 테스트"""
        config = TradingConfig()
        result = config.update_stock_priority("999999", 1)
        assert result is False
