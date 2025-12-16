"""
Backtest Engine - 백테스트 엔진 구현 (DIP 준수)
"""
import logging
from typing import List, Optional

from ..domain.interfaces import IBacktestEngine, IHistoricalDataProvider, IBacktestStrategy
from ..domain.models import DailyPrice, MinutePrice
from .models import BacktestResult, TradeRecord, TradeType
from .strategies import get_strategy, VolatilityBreakoutStrategy

logger = logging.getLogger(__name__)


class BacktestEngine(IBacktestEngine):
    """백테스트 엔진

    주입받은 데이터 제공자와 전략을 사용하여 백테스트를 수행합니다.
    """

    def __init__(self, data_provider: IHistoricalDataProvider):
        self._data_provider = data_provider

    def run(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        initial_capital: int,
        strategy: str,
        strategy_params: dict,
        stock_name: str = "",
        use_minute_data: bool = False,
    ) -> BacktestResult:
        """백테스트 실행

        Args:
            stock_code: 종목코드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            initial_capital: 초기 자본금
            strategy: 전략 종류 (range_trading, volatility_breakout)
            strategy_params: 전략 파라미터
            stock_name: 종목명 (선택)
            use_minute_data: 분봉 데이터 사용 여부

        Returns:
            백테스트 결과
        """
        data_type = "분봉" if use_minute_data else "일봉"
        logger.info(
            f"백테스트 시작: {stock_code} ({start_date} ~ {end_date}), "
            f"전략: {strategy}, 자본금: {initial_capital:,}원, 데이터: {data_type}"
        )

        # 1. 데이터 조회
        daily_data = self._data_provider.get_daily_data(stock_code, start_date, end_date)
        if not daily_data:
            logger.warning(f"일별 데이터가 없습니다: {stock_code}")
            return self._create_empty_result(
                stock_code, stock_name, start_date, end_date,
                strategy, initial_capital, strategy_params
            )

        # 2. 전략 인스턴스 생성
        strategy_instance = get_strategy(strategy)

        # 3. 시뮬레이션 실행
        if use_minute_data:
            result = self._simulate_minute(
                daily_data=daily_data,
                stock_code=stock_code,
                stock_name=stock_name,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                strategy_name=strategy,
                strategy_instance=strategy_instance,
                strategy_params=strategy_params,
            )
        else:
            result = self._simulate(
                daily_data=daily_data,
                stock_code=stock_code,
                stock_name=stock_name,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                strategy_name=strategy,
                strategy_instance=strategy_instance,
                strategy_params=strategy_params,
            )

        logger.info(
            f"백테스트 완료: 수익률 {result.total_return_rate:.2f}%, "
            f"총 거래 {result.total_trades}회"
        )

        return result

    def _simulate(
        self,
        daily_data: List[DailyPrice],
        stock_code: str,
        stock_name: str,
        start_date: str,
        end_date: str,
        initial_capital: int,
        strategy_name: str,
        strategy_instance: IBacktestStrategy,
        strategy_params: dict,
    ) -> BacktestResult:
        """시뮬레이션 수행"""
        # 상태 초기화
        cash = initial_capital
        position = 0  # 보유 수량
        avg_buy_price = 0  # 평균 매수가
        trades: List[TradeRecord] = []
        peak_capital = initial_capital
        max_drawdown = 0.0

        for i, data in enumerate(daily_data):
            prev_data = daily_data[i - 1] if i > 0 else None

            # 현재 자본 평가
            current_capital = cash + position * data.close_price

            # 최대 낙폭 계산
            if current_capital > peak_capital:
                peak_capital = current_capital
            drawdown = ((peak_capital - current_capital) / peak_capital) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

            # 매수 조건 확인 (미보유 상태)
            if position == 0:
                if strategy_instance.should_buy(
                    data.open_price, data, prev_data, position, strategy_params
                ):
                    # 매수 가격 결정
                    buy_price = self._get_buy_price(
                        strategy_instance, data, prev_data, strategy_params
                    )

                    if buy_price > 0 and buy_price <= cash:
                        # 매수 가능 수량 계산
                        quantity = cash // buy_price
                        if quantity > 0:
                            buy_amount = buy_price * quantity
                            cash -= buy_amount
                            position = quantity
                            avg_buy_price = buy_price

                            trades.append(
                                TradeRecord(
                                    date=data.date,
                                    trade_type=TradeType.BUY,
                                    price=buy_price,
                                    quantity=quantity,
                                    amount=buy_amount,
                                    reason=self._get_buy_reason(strategy_name, strategy_params, data, prev_data),
                                )
                            )

            # 매도 조건 확인 (보유 상태)
            elif position > 0:
                should_sell = strategy_instance.should_sell(
                    data.close_price, data, avg_buy_price, position, strategy_params
                )

                # VB 전략의 경우 장마감 매도 체크
                is_last_day = (i == len(daily_data) - 1)
                is_vb_close = (
                    strategy_name == "volatility_breakout" and
                    strategy_params.get("sell_at_close", True) and
                    is_last_day
                )

                if should_sell or is_vb_close:
                    # 매도 가격 및 사유 결정
                    sell_price, sell_reason = self._get_sell_price_and_reason(
                        strategy_name, strategy_instance, data,
                        avg_buy_price, strategy_params, is_vb_close
                    )

                    sell_amount = sell_price * position
                    profit_loss = (sell_price - avg_buy_price) * position
                    profit_rate = ((sell_price - avg_buy_price) / avg_buy_price) * 100

                    trades.append(
                        TradeRecord(
                            date=data.date,
                            trade_type=TradeType.SELL,
                            price=sell_price,
                            quantity=position,
                            amount=sell_amount,
                            profit_loss=profit_loss,
                            profit_rate=profit_rate,
                            reason=sell_reason,
                        )
                    )

                    cash += sell_amount
                    position = 0
                    avg_buy_price = 0

        # 최종 결과 계산
        final_capital = cash + position * daily_data[-1].close_price if daily_data else cash
        total_profit_loss = final_capital - initial_capital
        total_return_rate = (total_profit_loss / initial_capital) * 100 if initial_capital > 0 else 0

        # 거래 통계
        sell_trades = [t for t in trades if t.trade_type == TradeType.SELL]
        winning_trades = len([t for t in sell_trades if t.profit_loss > 0])
        losing_trades = len([t for t in sell_trades if t.profit_loss <= 0])
        win_rate = (winning_trades / len(sell_trades) * 100) if sell_trades else 0

        return BacktestResult(
            stock_code=stock_code,
            stock_name=stock_name or stock_code,
            start_date=start_date,
            end_date=end_date,
            strategy=strategy_name,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_trades=len(trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_profit_loss=total_profit_loss,
            total_return_rate=total_return_rate,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            trades=trades,
            strategy_params=strategy_params,
        )

    def _simulate_minute(
        self,
        daily_data: List[DailyPrice],
        stock_code: str,
        stock_name: str,
        start_date: str,
        end_date: str,
        initial_capital: int,
        strategy_name: str,
        strategy_instance: IBacktestStrategy,
        strategy_params: dict,
    ) -> BacktestResult:
        """분봉 기반 시뮬레이션 수행"""
        # 상태 초기화
        cash = initial_capital
        position = 0  # 보유 수량
        avg_buy_price = 0  # 평균 매수가
        trades: List[TradeRecord] = []
        peak_capital = initial_capital
        max_drawdown = 0.0
        minute_data_cache: List[MinutePrice] = []

        for day_idx, day_data in enumerate(daily_data):
            prev_day = daily_data[day_idx - 1] if day_idx > 0 else None

            # 해당 날짜의 분봉 데이터 조회
            minute_data = self._data_provider.get_minute_data(stock_code, day_data.date)

            if not minute_data:
                # 분봉 데이터가 없으면 일봉 기준으로 처리
                continue

            minute_data_cache.extend(minute_data)

            is_last_day = (day_idx == len(daily_data) - 1)

            for min_idx, min_data in enumerate(minute_data):
                current_price = min_data.close_price

                # 현재 자본 평가
                current_capital = cash + position * current_price

                # 최대 낙폭 계산
                if current_capital > peak_capital:
                    peak_capital = current_capital
                drawdown = ((peak_capital - current_capital) / peak_capital) * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

                # 장마감 시간 확인 (15:30)
                is_market_close = min_data.time[:4] >= "1530"

                # 매수 조건 확인 (미보유 상태)
                if position == 0:
                    buy_price = self._check_minute_buy(
                        strategy_name, strategy_params,
                        min_data, day_data, prev_day, cash
                    )

                    if buy_price > 0:
                        quantity = cash // buy_price
                        if quantity > 0:
                            buy_amount = buy_price * quantity
                            cash -= buy_amount
                            position = quantity
                            avg_buy_price = buy_price

                            trades.append(
                                TradeRecord(
                                    date=min_data.datetime,  # YYYYMMDDHHMMSS
                                    trade_type=TradeType.BUY,
                                    price=buy_price,
                                    quantity=quantity,
                                    amount=buy_amount,
                                    reason=self._get_minute_buy_reason(
                                        strategy_name, strategy_params, day_data, prev_day
                                    ),
                                )
                            )

                # 매도 조건 확인 (보유 상태)
                elif position > 0:
                    sell_result = self._check_minute_sell(
                        strategy_name, strategy_params,
                        min_data, day_data, avg_buy_price, is_market_close, is_last_day
                    )

                    if sell_result:
                        sell_price, sell_reason = sell_result
                        sell_amount = sell_price * position
                        profit_loss = (sell_price - avg_buy_price) * position
                        profit_rate = ((sell_price - avg_buy_price) / avg_buy_price) * 100

                        trades.append(
                            TradeRecord(
                                date=min_data.datetime,
                                trade_type=TradeType.SELL,
                                price=sell_price,
                                quantity=position,
                                amount=sell_amount,
                                profit_loss=profit_loss,
                                profit_rate=profit_rate,
                                reason=sell_reason,
                            )
                        )

                        cash += sell_amount
                        position = 0
                        avg_buy_price = 0

        # 최종 결과 계산
        last_price = minute_data_cache[-1].close_price if minute_data_cache else (
            daily_data[-1].close_price if daily_data else 0
        )
        final_capital = cash + position * last_price
        total_profit_loss = final_capital - initial_capital
        total_return_rate = (total_profit_loss / initial_capital) * 100 if initial_capital > 0 else 0

        # 거래 통계
        sell_trades = [t for t in trades if t.trade_type == TradeType.SELL]
        winning_trades = len([t for t in sell_trades if t.profit_loss > 0])
        losing_trades = len([t for t in sell_trades if t.profit_loss <= 0])
        win_rate = (winning_trades / len(sell_trades) * 100) if sell_trades else 0

        return BacktestResult(
            stock_code=stock_code,
            stock_name=stock_name or stock_code,
            start_date=start_date,
            end_date=end_date,
            strategy=strategy_name,
            initial_capital=initial_capital,
            final_capital=final_capital,
            total_trades=len(trades),
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            total_profit_loss=total_profit_loss,
            total_return_rate=total_return_rate,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            trades=trades,
            strategy_params=strategy_params,
            minute_prices=[mp for mp in minute_data_cache],  # 차트용 분봉 데이터
        )

    def _check_minute_buy(
        self,
        strategy_name: str,
        params: dict,
        minute_data: MinutePrice,
        day_data: DailyPrice,
        prev_day: Optional[DailyPrice],
        available_cash: int,
    ) -> int:
        """분봉 기준 매수 조건 확인 및 매수가 반환 (0이면 매수 안함)"""
        current_price = minute_data.close_price

        if strategy_name == "range_trading":
            buy_price = params.get("buy_price", 0)
            if buy_price > 0 and current_price <= buy_price:
                return buy_price

        elif strategy_name == "volatility_breakout":
            if prev_day:
                k = params.get("k", 0.5)
                volatility = prev_day.high_price - prev_day.low_price
                target_price = int(day_data.open_price + volatility * k)

                # 현재가가 목표가를 돌파하면 매수
                if current_price >= target_price:
                    return current_price

        return 0

    def _check_minute_sell(
        self,
        strategy_name: str,
        params: dict,
        minute_data: MinutePrice,
        day_data: DailyPrice,
        buy_price: int,
        is_market_close: bool,
        is_last_day: bool,
    ) -> Optional[tuple[int, str]]:
        """분봉 기준 매도 조건 확인 및 (매도가, 사유) 반환 (None이면 매도 안함)"""
        current_price = minute_data.close_price

        if strategy_name == "range_trading":
            sell_price = params.get("sell_price", 0)
            if sell_price > 0 and current_price >= sell_price:
                return (sell_price, f"매도가({sell_price:,}원) 도달")

        elif strategy_name == "volatility_breakout":
            # 익절 확인
            target_rate = params.get("target_profit_rate", 2.0)
            profit_rate = ((current_price - buy_price) / buy_price) * 100
            if profit_rate >= target_rate:
                return (current_price, f"익절({profit_rate:.1f}%)")

            # 손절 확인
            stop_rate = params.get("stop_loss_rate", -2.0)
            if profit_rate <= stop_rate:
                return (current_price, f"손절({profit_rate:.1f}%)")

            # 장마감 매도
            if is_market_close and params.get("sell_at_close", True):
                return (current_price, "장마감 매도")

        # 마지막 날 강제 청산
        if is_last_day and is_market_close:
            return (current_price, "백테스트 종료")

        return None

    def _get_minute_buy_reason(
        self,
        strategy_name: str,
        params: dict,
        day_data: DailyPrice,
        prev_day: Optional[DailyPrice],
    ) -> str:
        """분봉 매수 사유 생성"""
        if strategy_name == "range_trading":
            return f"매수가({params.get('buy_price', 0):,}원) 도달"
        elif strategy_name == "volatility_breakout":
            if prev_day:
                k = params.get("k", 0.5)
                volatility = prev_day.high_price - prev_day.low_price
                target = int(day_data.open_price + volatility * k)
                return f"목표가({target:,}원) 돌파 (K={k})"
        return "매수"

    def _get_buy_price(
        self,
        strategy: IBacktestStrategy,
        data: DailyPrice,
        prev_data: Optional[DailyPrice],
        params: dict,
    ) -> int:
        """매수가 결정"""
        target_price = strategy.get_buy_price(data, prev_data, params)

        # 실제로 체결될 가격 결정 (시뮬레이션)
        if target_price <= data.low_price:
            return target_price
        elif target_price <= data.high_price:
            return target_price
        return 0

    def _get_buy_reason(
        self,
        strategy_name: str,
        params: dict,
        data: DailyPrice,
        prev_data: Optional[DailyPrice],
    ) -> str:
        """매수 사유 생성"""
        if strategy_name == "range_trading":
            return f"매수가({params.get('buy_price', 0):,}원) 도달"
        elif strategy_name == "volatility_breakout":
            if prev_data:
                k = params.get("k", 0.5)
                volatility = prev_data.high_price - prev_data.low_price
                target = int(data.open_price + volatility * k)
                return f"목표가({target:,}원) 돌파 (K={k})"
        return "매수"

    def _get_sell_price_and_reason(
        self,
        strategy_name: str,
        strategy: IBacktestStrategy,
        data: DailyPrice,
        buy_price: int,
        params: dict,
        is_forced_close: bool,
    ) -> tuple[int, str]:
        """매도가 및 사유 결정"""
        if is_forced_close:
            return data.close_price, "장마감(종료일)"

        if strategy_name == "range_trading":
            sell_price = params.get("sell_price", 0)
            return sell_price, f"매도가({sell_price:,}원) 도달"

        elif strategy_name == "volatility_breakout":
            if isinstance(strategy, VolatilityBreakoutStrategy):
                return strategy.get_sell_price(buy_price, data, params)

        return data.close_price, "매도"

    def _create_empty_result(
        self,
        stock_code: str,
        stock_name: str,
        start_date: str,
        end_date: str,
        strategy: str,
        initial_capital: int,
        strategy_params: dict,
    ) -> BacktestResult:
        """빈 결과 생성 (데이터 없음)"""
        return BacktestResult(
            stock_code=stock_code,
            stock_name=stock_name or stock_code,
            start_date=start_date,
            end_date=end_date,
            strategy=strategy,
            initial_capital=initial_capital,
            final_capital=initial_capital,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            total_profit_loss=0,
            total_return_rate=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            trades=[],
            strategy_params=strategy_params,
        )
