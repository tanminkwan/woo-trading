"""
Backtest Module Tests - 백테스트 기능 테스트
"""
import pytest
from datetime import datetime

from src.domain.models import DailyPrice
from src.backtest.models import BacktestResult, TradeRecord, TradeType
from src.backtest.strategies import (
    RangeTradingStrategy,
    VolatilityBreakoutStrategy,
    get_strategy,
)
from src.backtest.data_provider import (
    MockHistoricalDataProvider,
    generate_sample_data,
)
from src.backtest.engine import BacktestEngine


# ============ Test Fixtures ============

@pytest.fixture
def sample_daily_data():
    """테스트용 일별 데이터"""
    return [
        DailyPrice(date="20241201", close_price=50000, open_price=49500, high_price=51000, low_price=49000, volume=1000000),
        DailyPrice(date="20241202", close_price=51000, open_price=50000, high_price=52000, low_price=49500, volume=1200000),
        DailyPrice(date="20241203", close_price=49000, open_price=51000, high_price=51500, low_price=48500, volume=1500000),
        DailyPrice(date="20241204", close_price=52000, open_price=49000, high_price=53000, low_price=48000, volume=2000000),
        DailyPrice(date="20241205", close_price=53000, open_price=52000, high_price=54000, low_price=51000, volume=1800000),
    ]


@pytest.fixture
def range_strategy():
    """범위 매매 전략"""
    return RangeTradingStrategy()


@pytest.fixture
def vb_strategy():
    """변동성 돌파 전략"""
    return VolatilityBreakoutStrategy()


@pytest.fixture
def mock_provider(sample_daily_data):
    """Mock 데이터 제공자"""
    return MockHistoricalDataProvider(sample_daily_data)


# ============ TradeRecord Tests ============

class TestTradeRecord:
    def test_buy_record(self):
        """매수 기록 생성"""
        record = TradeRecord(
            date="20241201",
            trade_type=TradeType.BUY,
            price=50000,
            quantity=10,
            amount=500000,
            reason="테스트 매수",
        )
        assert record.trade_type == TradeType.BUY
        assert record.amount == 500000

    def test_sell_record_with_profit(self):
        """수익 매도 기록"""
        record = TradeRecord(
            date="20241202",
            trade_type=TradeType.SELL,
            price=55000,
            quantity=10,
            amount=550000,
            profit_loss=50000,
            profit_rate=10.0,
            reason="목표가 도달",
        )
        assert record.profit_loss == 50000
        assert record.profit_rate == 10.0

    def test_to_dict(self):
        """dict 변환"""
        record = TradeRecord(
            date="20241201",
            trade_type=TradeType.BUY,
            price=50000,
            quantity=10,
            amount=500000,
        )
        d = record.to_dict()
        assert d["일자"] == "20241201"
        assert d["구분"] == "매수"
        assert d["가격"] == 50000


# ============ BacktestResult Tests ============

class TestBacktestResult:
    def test_profitable_result(self):
        """수익 결과"""
        result = BacktestResult(
            stock_code="005930",
            stock_name="삼성전자",
            start_date="20241201",
            end_date="20241231",
            strategy="range_trading",
            initial_capital=1000000,
            final_capital=1100000,
            total_trades=4,
            winning_trades=3,
            losing_trades=1,
            total_profit_loss=100000,
            total_return_rate=10.0,
            max_drawdown=5.0,
            win_rate=75.0,
        )
        assert result.is_profitable == True
        assert result.total_return_rate == 10.0

    def test_losing_result(self):
        """손실 결과"""
        result = BacktestResult(
            stock_code="005930",
            stock_name="삼성전자",
            start_date="20241201",
            end_date="20241231",
            strategy="volatility_breakout",
            initial_capital=1000000,
            final_capital=900000,
            total_trades=2,
            winning_trades=0,
            losing_trades=1,
            total_profit_loss=-100000,
            total_return_rate=-10.0,
            max_drawdown=15.0,
            win_rate=0.0,
        )
        assert result.is_profitable == False

    def test_get_summary(self):
        """결과 요약"""
        result = BacktestResult(
            stock_code="005930",
            stock_name="삼성전자",
            start_date="20241201",
            end_date="20241231",
            strategy="range_trading",
            initial_capital=1000000,
            final_capital=1100000,
            total_trades=4,
            winning_trades=3,
            losing_trades=1,
            total_profit_loss=100000,
            total_return_rate=10.0,
            max_drawdown=5.0,
            win_rate=75.0,
        )
        summary = result.get_summary()
        assert "삼성전자" in summary
        assert "10.00%" in summary
        assert "75.0%" in summary


# ============ RangeTradingStrategy Tests ============

class TestRangeTradingStrategy:
    def test_should_buy_below_price(self, range_strategy, sample_daily_data):
        """매수가 이하 시 매수"""
        params = {"buy_price": 50000, "sell_price": 55000}
        result = range_strategy.should_buy(
            current_price=49000,
            daily_data=sample_daily_data[0],
            prev_data=None,
            position=0,
            params=params,
        )
        assert result == True

    def test_should_not_buy_above_price(self, range_strategy, sample_daily_data):
        """매수가 초과 시 미매수"""
        params = {"buy_price": 50000, "sell_price": 55000}
        result = range_strategy.should_buy(
            current_price=51000,
            daily_data=sample_daily_data[0],
            prev_data=None,
            position=0,
            params=params,
        )
        assert result == False

    def test_should_not_buy_with_position(self, range_strategy, sample_daily_data):
        """보유 중일 때 미매수"""
        params = {"buy_price": 50000, "sell_price": 55000}
        result = range_strategy.should_buy(
            current_price=49000,
            daily_data=sample_daily_data[0],
            prev_data=None,
            position=10,
            params=params,
        )
        assert result == False

    def test_should_sell_above_price(self, range_strategy, sample_daily_data):
        """매도가 이상 시 매도"""
        params = {"buy_price": 50000, "sell_price": 55000}
        result = range_strategy.should_sell(
            current_price=56000,
            daily_data=sample_daily_data[0],
            buy_price=50000,
            position=10,
            params=params,
        )
        assert result == True

    def test_should_not_sell_below_price(self, range_strategy, sample_daily_data):
        """매도가 미만 시 미매도"""
        params = {"buy_price": 50000, "sell_price": 55000}
        result = range_strategy.should_sell(
            current_price=54000,
            daily_data=sample_daily_data[0],
            buy_price=50000,
            position=10,
            params=params,
        )
        assert result == False

    def test_get_buy_price(self, range_strategy, sample_daily_data):
        """매수가 반환"""
        params = {"buy_price": 50000, "sell_price": 55000}
        price = range_strategy.get_buy_price(
            daily_data=sample_daily_data[0],
            prev_data=None,
            params=params,
        )
        assert price == 50000


# ============ VolatilityBreakoutStrategy Tests ============

class TestVolatilityBreakoutStrategy:
    def test_get_buy_price_calculation(self, vb_strategy, sample_daily_data):
        """목표가 계산"""
        # 전일: high=51000, low=49500, 변동성=1500
        # 당일: open=49000
        # 목표가 = 49000 + 1500 * 0.5 = 49750
        params = {"k": 0.5}
        price = vb_strategy.get_buy_price(
            daily_data=sample_daily_data[3],  # open=49000
            prev_data=sample_daily_data[2],  # high=51500, low=48500, volatility=3000
            params=params,
        )
        expected = 49000 + int((51500 - 48500) * 0.5)  # 49000 + 1500 = 50500
        assert price == expected

    def test_should_buy_target_reached(self, vb_strategy, sample_daily_data):
        """목표가 돌파 시 매수"""
        params = {"k": 0.5}
        # sample_daily_data[3]: open=49000, high=53000
        # prev: high=51500, low=48500 -> volatility=3000
        # target = 49000 + 1500 = 50500
        # high(53000) >= target(50500) -> should buy
        result = vb_strategy.should_buy(
            current_price=52000,
            daily_data=sample_daily_data[3],
            prev_data=sample_daily_data[2],
            position=0,
            params=params,
        )
        assert result == True

    def test_should_not_buy_no_prev_data(self, vb_strategy, sample_daily_data):
        """전일 데이터 없으면 미매수"""
        params = {"k": 0.5}
        result = vb_strategy.should_buy(
            current_price=52000,
            daily_data=sample_daily_data[0],
            prev_data=None,
            position=0,
            params=params,
        )
        assert result == False

    def test_should_sell_profit_target(self, vb_strategy, sample_daily_data):
        """익절 도달 시 매도"""
        params = {"target_profit_rate": 2.0, "stop_loss_rate": -2.0}
        # buy_price=50000, target=51000 (2%)
        # high=54000 > 51000 -> should sell
        result = vb_strategy.should_sell(
            current_price=53000,
            daily_data=sample_daily_data[4],  # high=54000
            buy_price=50000,
            position=10,
            params=params,
        )
        assert result == True

    def test_should_sell_stop_loss(self, vb_strategy, sample_daily_data):
        """손절 도달 시 매도"""
        params = {"target_profit_rate": 2.0, "stop_loss_rate": -2.0}
        # buy_price=50000, stop=49000 (-2%)
        # low=48500 < 49000 -> should sell
        result = vb_strategy.should_sell(
            current_price=49000,
            daily_data=sample_daily_data[2],  # low=48500
            buy_price=50000,
            position=10,
            params=params,
        )
        assert result == True

    def test_get_sell_price_profit(self, vb_strategy, sample_daily_data):
        """익절 매도가"""
        params = {"target_profit_rate": 2.0, "stop_loss_rate": -2.0}
        price, reason = vb_strategy.get_sell_price(
            buy_price=50000,
            daily_data=sample_daily_data[4],  # high=54000
            params=params,
        )
        assert price == 51000  # 50000 * 1.02
        assert reason == "익절"

    def test_get_sell_price_stop_loss(self, vb_strategy, sample_daily_data):
        """손절 매도가"""
        params = {"target_profit_rate": 5.0, "stop_loss_rate": -2.0}
        price, reason = vb_strategy.get_sell_price(
            buy_price=50000,
            daily_data=sample_daily_data[2],  # low=48500, high=51500
            params=params,
        )
        assert price == 49000  # 50000 * 0.98
        assert reason == "손절"


# ============ Strategy Factory Tests ============

class TestStrategyFactory:
    def test_get_range_strategy(self):
        """범위 매매 전략 생성"""
        strategy = get_strategy("range_trading")
        assert isinstance(strategy, RangeTradingStrategy)

    def test_get_vb_strategy(self):
        """변동성 돌파 전략 생성"""
        strategy = get_strategy("volatility_breakout")
        assert isinstance(strategy, VolatilityBreakoutStrategy)

    def test_unknown_strategy_raises(self):
        """알 수 없는 전략 예외"""
        with pytest.raises(ValueError):
            get_strategy("unknown_strategy")


# ============ MockHistoricalDataProvider Tests ============

class TestMockHistoricalDataProvider:
    def test_get_daily_data(self, mock_provider):
        """데이터 조회"""
        data = mock_provider.get_daily_data("005930", "20241201", "20241205")
        assert len(data) == 5
        assert data[0].date == "20241201"
        assert data[-1].date == "20241205"

    def test_filter_by_date_range(self, mock_provider):
        """기간 필터링"""
        data = mock_provider.get_daily_data("005930", "20241202", "20241204")
        assert len(data) == 3
        assert data[0].date == "20241202"
        assert data[-1].date == "20241204"

    def test_empty_result(self):
        """빈 결과"""
        provider = MockHistoricalDataProvider([])
        data = provider.get_daily_data("005930", "20241201", "20241205")
        assert len(data) == 0


# ============ generate_sample_data Tests ============

class TestGenerateSampleData:
    def test_generate_data(self):
        """샘플 데이터 생성"""
        data = generate_sample_data("20241201", "20241207", base_price=50000)
        # 주말 제외하면 5일
        assert len(data) == 5
        assert data[0].date == "20241202"  # 20241201은 일요일

    def test_data_consistency(self):
        """데이터 일관성"""
        data = generate_sample_data("20241202", "20241206", base_price=50000)
        for d in data:
            assert d.high_price >= d.open_price
            assert d.high_price >= d.close_price
            assert d.low_price <= d.open_price
            assert d.low_price <= d.close_price


# ============ BacktestEngine Tests ============

class TestBacktestEngine:
    def test_range_trading_backtest(self, mock_provider):
        """범위 매매 백테스트"""
        engine = BacktestEngine(mock_provider)
        result = engine.run(
            stock_code="005930",
            start_date="20241201",
            end_date="20241205",
            initial_capital=1000000,
            strategy="range_trading",
            strategy_params={"buy_price": 49000, "sell_price": 52000},
            stock_name="삼성전자",
        )

        assert result.stock_code == "005930"
        assert result.strategy == "range_trading"
        assert result.initial_capital == 1000000

    def test_vb_backtest(self, mock_provider):
        """변동성 돌파 백테스트"""
        engine = BacktestEngine(mock_provider)
        result = engine.run(
            stock_code="005930",
            start_date="20241201",
            end_date="20241205",
            initial_capital=1000000,
            strategy="volatility_breakout",
            strategy_params={
                "k": 0.5,
                "target_profit_rate": 2.0,
                "stop_loss_rate": -2.0,
                "sell_at_close": True,
            },
            stock_name="삼성전자",
        )

        assert result.stock_code == "005930"
        assert result.strategy == "volatility_breakout"

    def test_empty_data_result(self):
        """데이터 없는 경우"""
        provider = MockHistoricalDataProvider([])
        engine = BacktestEngine(provider)
        result = engine.run(
            stock_code="005930",
            start_date="20241201",
            end_date="20241205",
            initial_capital=1000000,
            strategy="range_trading",
            strategy_params={"buy_price": 49000, "sell_price": 52000},
        )

        assert result.total_trades == 0
        assert result.final_capital == 1000000

    def test_no_trades_when_conditions_not_met(self, sample_daily_data):
        """조건 미충족 시 거래 없음"""
        provider = MockHistoricalDataProvider(sample_daily_data)
        engine = BacktestEngine(provider)
        result = engine.run(
            stock_code="005930",
            start_date="20241201",
            end_date="20241205",
            initial_capital=1000000,
            strategy="range_trading",
            strategy_params={"buy_price": 40000, "sell_price": 60000},  # 도달 불가능 가격
        )

        assert result.total_trades == 0
        assert result.final_capital == 1000000

    def test_max_drawdown_calculation(self, mock_provider):
        """최대 낙폭 계산"""
        engine = BacktestEngine(mock_provider)
        result = engine.run(
            stock_code="005930",
            start_date="20241201",
            end_date="20241205",
            initial_capital=1000000,
            strategy="volatility_breakout",
            strategy_params={
                "k": 0.5,
                "target_profit_rate": 10.0,  # 높은 목표로 손절 유도
                "stop_loss_rate": -1.0,
                "sell_at_close": True,
            },
        )

        # 최대 낙폭은 0 이상
        assert result.max_drawdown >= 0


# ============ Integration Tests ============

class TestBacktestIntegration:
    def test_full_backtest_flow(self):
        """전체 백테스트 플로우"""
        # 1. 샘플 데이터 생성
        data = generate_sample_data("20241201", "20241231", base_price=50000)

        # 2. 데이터 제공자 설정
        provider = MockHistoricalDataProvider(data)

        # 3. 엔진 생성 및 실행
        engine = BacktestEngine(provider)
        result = engine.run(
            stock_code="005930",
            start_date="20241201",
            end_date="20241231",
            initial_capital=1000000,
            strategy="volatility_breakout",
            strategy_params={
                "k": 0.5,
                "target_profit_rate": 2.0,
                "stop_loss_rate": -2.0,
                "sell_at_close": True,
            },
            stock_name="삼성전자",
        )

        # 4. 결과 검증
        assert result.stock_name == "삼성전자"
        assert result.initial_capital == 1000000
        assert result.final_capital > 0
        assert 0 <= result.win_rate <= 100

    def test_backtest_with_different_strategies(self):
        """다양한 전략 백테스트"""
        data = generate_sample_data("20241201", "20241210", base_price=50000)
        provider = MockHistoricalDataProvider(data)
        engine = BacktestEngine(provider)

        # 범위 매매
        result1 = engine.run(
            stock_code="005930",
            start_date="20241201",
            end_date="20241210",
            initial_capital=1000000,
            strategy="range_trading",
            strategy_params={"buy_price": 49000, "sell_price": 51000},
        )

        # 변동성 돌파
        result2 = engine.run(
            stock_code="005930",
            start_date="20241201",
            end_date="20241210",
            initial_capital=1000000,
            strategy="volatility_breakout",
            strategy_params={
                "k": 0.5,
                "target_profit_rate": 1.0,
                "stop_loss_rate": -1.0,
            },
        )

        # 두 전략 모두 실행됨
        assert result1.strategy == "range_trading"
        assert result2.strategy == "volatility_breakout"
