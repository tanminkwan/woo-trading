"""
Backtest Strategies - 백테스트 전략 구현 (OCP 준수)
"""
from typing import Optional

from ..domain.interfaces import IBacktestStrategy
from ..domain.models import DailyPrice


class RangeTradingStrategy(IBacktestStrategy):
    """범위 매매 전략 시뮬레이터

    buy_price 이하일 때 매수, sell_price 이상일 때 매도
    """

    def should_buy(
        self,
        current_price: int,
        daily_data: DailyPrice,
        prev_data: Optional[DailyPrice],
        position: int,
        params: dict,
    ) -> bool:
        """매수 조건: 당일 저가가 buy_price 이하이고 미보유 상태"""
        buy_price = params.get("buy_price", 0)
        if position > 0 or buy_price <= 0:
            return False
        # 일봉: 저가가 매수가 이하면 매수 가능
        return daily_data.low_price <= buy_price

    def should_sell(
        self,
        current_price: int,
        daily_data: DailyPrice,
        buy_price: int,
        position: int,
        params: dict,
    ) -> bool:
        """매도 조건: 당일 고가가 sell_price 이상이고 보유 중"""
        sell_price = params.get("sell_price", 0)
        if position <= 0 or sell_price <= 0:
            return False
        # 일봉: 고가가 매도가 이상이면 매도 가능
        return daily_data.high_price >= sell_price

    def get_buy_price(
        self,
        daily_data: DailyPrice,
        prev_data: Optional[DailyPrice],
        params: dict,
    ) -> int:
        """매수가: buy_price 설정값"""
        return params.get("buy_price", 0)


class VolatilityBreakoutStrategy(IBacktestStrategy):
    """변동성 돌파 전략 시뮬레이터

    목표가 = 시가 + (전일 고가 - 전일 저가) * K
    목표가 돌파 시 매수, 익절/손절/장마감 시 매도
    """

    def should_buy(
        self,
        current_price: int,
        daily_data: DailyPrice,
        prev_data: Optional[DailyPrice],
        position: int,
        params: dict,
    ) -> bool:
        """매수 조건: 현재가가 목표가 이상이고 미보유 상태"""
        if position > 0 or prev_data is None:
            return False

        target_price = self.get_buy_price(daily_data, prev_data, params)
        if target_price <= 0:
            return False

        # 당일 고가가 목표가 이상이면 매수 가능
        return daily_data.high_price >= target_price

    def should_sell(
        self,
        current_price: int,
        daily_data: DailyPrice,
        buy_price: int,
        position: int,
        params: dict,
    ) -> bool:
        """매도 조건: 익절/손절 도달 또는 장마감"""
        if position <= 0 or buy_price <= 0:
            return False

        target_profit_rate = params.get("target_profit_rate", 2.0)
        stop_loss_rate = params.get("stop_loss_rate", -2.0)

        # 당일 수익률 계산 (고가/저가 기준)
        high_profit_rate = ((daily_data.high_price - buy_price) / buy_price) * 100
        low_profit_rate = ((daily_data.low_price - buy_price) / buy_price) * 100

        # 익절가 도달
        if high_profit_rate >= target_profit_rate:
            return True

        # 손절가 도달
        if low_profit_rate <= stop_loss_rate:
            return True

        return False

    def get_buy_price(
        self,
        daily_data: DailyPrice,
        prev_data: Optional[DailyPrice],
        params: dict,
    ) -> int:
        """목표가 계산: 시가 + (전일 고가 - 전일 저가) * K"""
        if prev_data is None:
            return 0

        k = params.get("k", 0.5)
        volatility = prev_data.high_price - prev_data.low_price
        target_price = int(daily_data.open_price + volatility * k)
        return target_price

    def get_sell_price(
        self,
        buy_price: int,
        daily_data: DailyPrice,
        params: dict,
    ) -> tuple[int, str]:
        """매도가 및 사유 계산

        Returns:
            (매도가, 사유)
        """
        target_profit_rate = params.get("target_profit_rate", 2.0)
        stop_loss_rate = params.get("stop_loss_rate", -2.0)

        target_price = int(buy_price * (1 + target_profit_rate / 100))
        stop_price = int(buy_price * (1 + stop_loss_rate / 100))

        # 익절가 도달 여부 (고가 기준)
        if daily_data.high_price >= target_price:
            return target_price, "익절"

        # 손절가 도달 여부 (저가 기준)
        if daily_data.low_price <= stop_price:
            return stop_price, "손절"

        # 장마감 (종가 매도)
        return daily_data.close_price, "장마감"


# 전략 팩토리 (DIP 준수)
def get_strategy(strategy_name: str) -> IBacktestStrategy:
    """전략 이름으로 전략 인스턴스 반환"""
    strategies = {
        "range_trading": RangeTradingStrategy(),
        "volatility_breakout": VolatilityBreakoutStrategy(),
    }
    strategy = strategies.get(strategy_name)
    if strategy is None:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    return strategy
