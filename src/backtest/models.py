"""
Backtest Models - 백테스트 결과 및 거래 기록 모델
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..domain.models import MinutePrice


class TradeType(Enum):
    """거래 유형"""
    BUY = "buy"
    SELL = "sell"


@dataclass
class TradeRecord:
    """개별 거래 기록"""
    date: str
    trade_type: TradeType
    price: int
    quantity: int
    amount: int
    profit_loss: int = 0
    profit_rate: float = 0.0
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "일자": self.date,
            "구분": "매수" if self.trade_type == TradeType.BUY else "매도",
            "가격": self.price,
            "수량": self.quantity,
            "금액": self.amount,
            "손익": self.profit_loss,
            "수익률": f"{self.profit_rate:.2f}%",
            "사유": self.reason,
        }


@dataclass
class BacktestResult:
    """백테스트 결과"""
    stock_code: str
    stock_name: str
    start_date: str
    end_date: str
    strategy: str
    initial_capital: int
    final_capital: int
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_profit_loss: int
    total_return_rate: float
    max_drawdown: float
    win_rate: float
    trades: List[TradeRecord] = field(default_factory=list)
    strategy_params: dict = field(default_factory=dict)
    minute_prices: List = field(default_factory=list)  # 분봉 데이터 (차트용)

    @property
    def is_profitable(self) -> bool:
        return self.total_profit_loss > 0

    def to_dict(self) -> dict:
        return {
            "종목코드": self.stock_code,
            "종목명": self.stock_name,
            "시작일": self.start_date,
            "종료일": self.end_date,
            "전략": self.strategy,
            "초기자본": self.initial_capital,
            "최종자본": self.final_capital,
            "총거래횟수": self.total_trades,
            "수익거래": self.winning_trades,
            "손실거래": self.losing_trades,
            "총손익": self.total_profit_loss,
            "수익률": f"{self.total_return_rate:.2f}%",
            "최대낙폭": f"{self.max_drawdown:.2f}%",
            "승률": f"{self.win_rate:.2f}%",
            "전략파라미터": self.strategy_params,
            "거래내역": [t.to_dict() for t in self.trades],
        }

    def get_summary(self) -> str:
        """백테스트 결과 요약 문자열"""
        summary = f"""
========================================
백테스트 결과 요약
========================================
종목: {self.stock_name} ({self.stock_code})
기간: {self.start_date} ~ {self.end_date}
전략: {self.strategy}
----------------------------------------
초기 자본: {self.initial_capital:,}원
최종 자본: {self.final_capital:,}원
총 손익: {self.total_profit_loss:,}원 ({self.total_return_rate:+.2f}%)
----------------------------------------
총 거래: {self.total_trades}회
수익 거래: {self.winning_trades}회
손실 거래: {self.losing_trades}회
승률: {self.win_rate:.1f}%
최대 낙폭: {self.max_drawdown:.2f}%
========================================
"""
        return summary
