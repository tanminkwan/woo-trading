"""
Trading Engine Tests
"""
import pytest
import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock, patch
from src.engine.trading_engine import TradingEngine, EngineStatus, TradeLog
from src.engine.config_parser import TradingConfig, StockConfig
from src.domain.models import StockPrice, Balance, Holdings, AccountSummary, Deposit, OrderResult


class TestTradeLog:
    """TradeLog 테스트"""

    def test_to_dict(self):
        from datetime import datetime
        log = TradeLog(
            timestamp=datetime(2025, 12, 16, 10, 0, 0),
            stock_code="005930",
            stock_name="삼성전자",
            action="buy",
            quantity=10,
            price=50000,
            success=True,
            message="주문 성공",
        )

        result = log.to_dict()
        assert result["stock_code"] == "005930"
        assert result["action"] == "buy"
        assert result["quantity"] == 10
        assert result["success"] is True


class TestTradingEngine:
    """TradingEngine 테스트"""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.is_authenticated = True
        client.authenticate.return_value = True
        return client

    @pytest.fixture
    def config(self):
        return TradingConfig(
            default_interval=60,
            max_daily_trades=10,
            stocks=[
                StockConfig("005930", "삼성전자", 1000000, 50000, 60000, enabled=True),
            ]
        )

    @pytest.fixture
    def engine(self, mock_client, config):
        return TradingEngine(mock_client, config)

    def test_initial_status(self, engine):
        assert engine.status == EngineStatus.STOPPED

    def test_start_engine(self, engine):
        result = engine.start()
        assert result is True
        assert engine.status == EngineStatus.RUNNING
        engine.stop()

    def test_stop_engine(self, engine):
        engine.start()
        engine.stop()
        assert engine.status == EngineStatus.STOPPED

    def test_pause_engine(self, engine):
        engine.start()
        engine.pause()
        assert engine.status == EngineStatus.PAUSED
        engine.stop()

    def test_resume_engine(self, engine):
        engine.start()
        engine.pause()
        engine.resume()
        assert engine.status == EngineStatus.RUNNING
        engine.stop()

    def test_start_already_running(self, engine):
        engine.start()
        result = engine.start()
        assert result is False
        engine.stop()

    def test_reload_config(self, engine):
        new_config = TradingConfig(
            default_interval=30,
            max_daily_trades=5,
        )
        engine.reload_config(new_config)
        assert engine.config.default_interval == 30
        assert engine.config.max_daily_trades == 5

    def test_get_summary(self, engine):
        summary = engine.get_summary()
        assert "status" in summary
        assert "daily_trade_count" in summary
        assert "enabled_stocks" in summary
        assert "total_stocks" in summary

    def test_add_callback(self, engine):
        callback = MagicMock()
        engine.add_callback(callback)
        assert callback in engine._callbacks

    def test_trade_logs_empty_initially(self, engine):
        assert len(engine.trade_logs) == 0

    def test_stock_status_empty_initially(self, engine):
        assert len(engine.stock_status) == 0


class TestEngineStatus:
    """EngineStatus 열거형 테스트"""

    def test_status_values(self):
        assert EngineStatus.STOPPED.value == "stopped"
        assert EngineStatus.RUNNING.value == "running"
        assert EngineStatus.PAUSED.value == "paused"
