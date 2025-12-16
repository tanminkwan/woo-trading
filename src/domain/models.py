"""
Domain Models - 비즈니스 엔티티 정의
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from datetime import datetime


class OrderType(Enum):
    """주문 유형"""
    LIMIT = "00"      # 지정가
    MARKET = "01"     # 시장가


class OrderSide(Enum):
    """주문 방향"""
    BUY = "buy"
    SELL = "sell"


@dataclass(frozen=True)
class StockPrice:
    """주식 현재가 정보"""
    stock_code: str
    current_price: int
    change_price: int
    change_rate: float
    open_price: int
    high_price: int
    low_price: int
    volume: int

    def to_dict(self) -> dict:
        return {
            "종목코드": self.stock_code,
            "현재가": self.current_price,
            "전일대비": self.change_price,
            "등락률": self.change_rate,
            "시가": self.open_price,
            "고가": self.high_price,
            "저가": self.low_price,
            "거래량": self.volume,
        }


@dataclass(frozen=True)
class AskingPrice:
    """호가 정보"""
    sell_prices: List[int]
    buy_prices: List[int]
    sell_volumes: List[int]
    buy_volumes: List[int]

    def to_dict(self) -> dict:
        result = {}
        for i, (price, vol) in enumerate(zip(self.sell_prices, self.sell_volumes), 1):
            result[f"매도호가{i}"] = price
            result[f"매도잔량{i}"] = vol
        for i, (price, vol) in enumerate(zip(self.buy_prices, self.buy_volumes), 1):
            result[f"매수호가{i}"] = price
            result[f"매수잔량{i}"] = vol
        return result


@dataclass(frozen=True)
class DailyPrice:
    """일별 시세 정보"""
    date: str
    close_price: int
    open_price: int
    high_price: int
    low_price: int
    volume: int

    def to_dict(self) -> dict:
        return {
            "일자": self.date,
            "종가": self.close_price,
            "시가": self.open_price,
            "고가": self.high_price,
            "저가": self.low_price,
            "거래량": self.volume,
        }


@dataclass(frozen=True)
class MinutePrice:
    """분봉 시세 정보"""
    datetime: str  # YYYYMMDDHHMMSS
    close_price: int
    open_price: int
    high_price: int
    low_price: int
    volume: int

    @property
    def date(self) -> str:
        """날짜 (YYYYMMDD)"""
        return self.datetime[:8]

    @property
    def time(self) -> str:
        """시간 (HHMMSS)"""
        return self.datetime[8:]

    @property
    def time_formatted(self) -> str:
        """시간 (HH:MM)"""
        return f"{self.datetime[8:10]}:{self.datetime[10:12]}"

    def to_dict(self) -> dict:
        return {
            "일시": self.datetime,
            "종가": self.close_price,
            "시가": self.open_price,
            "고가": self.high_price,
            "저가": self.low_price,
            "거래량": self.volume,
        }


@dataclass(frozen=True)
class Holdings:
    """보유 종목 정보"""
    stock_code: str
    stock_name: str
    quantity: int
    avg_buy_price: int
    current_price: int
    eval_amount: int
    profit_loss: int
    profit_rate: float

    def to_dict(self) -> dict:
        return {
            "종목코드": self.stock_code,
            "종목명": self.stock_name,
            "보유수량": self.quantity,
            "매입평균가": self.avg_buy_price,
            "현재가": self.current_price,
            "평가금액": self.eval_amount,
            "평가손익": self.profit_loss,
            "수익률": self.profit_rate,
        }


@dataclass(frozen=True)
class AccountSummary:
    """계좌 요약 정보"""
    deposit: int
    total_buy_amount: int
    total_eval_amount: int
    total_profit_loss: int

    def to_dict(self) -> dict:
        return {
            "예수금총액": self.deposit,
            "총매입금액": self.total_buy_amount,
            "총평가금액": self.total_eval_amount,
            "총평가손익": self.total_profit_loss,
        }


@dataclass(frozen=True)
class Balance:
    """계좌 잔고 (보유종목 + 요약)"""
    holdings: List[Holdings]
    summary: AccountSummary


@dataclass(frozen=True)
class Deposit:
    """주문 가능 금액"""
    available_cash: int
    available_total: int

    def to_dict(self) -> dict:
        return {
            "주문가능현금": self.available_cash,
            "주문가능총액": self.available_total,
        }


@dataclass(frozen=True)
class OrderResult:
    """주문 결과"""
    success: bool
    order_no: Optional[str] = None
    order_time: Optional[str] = None
    message: str = ""

    def to_dict(self) -> dict:
        result = {"성공": self.success, "메시지": self.message}
        if self.order_no:
            result["주문번호"] = self.order_no
        if self.order_time:
            result["주문시각"] = self.order_time
        return result


@dataclass(frozen=True)
class OrderInfo:
    """주문 내역 정보"""
    order_no: str
    stock_code: str
    stock_name: str
    order_side: str
    order_qty: int
    order_price: int
    executed_qty: int
    executed_price: int
    order_time: str

    @property
    def is_executed(self) -> bool:
        return self.executed_qty == self.order_qty

    @property
    def status(self) -> str:
        if self.is_executed:
            return "체결완료"
        return f"미체결({self.executed_qty}/{self.order_qty})"

    def to_dict(self) -> dict:
        return {
            "주문번호": self.order_no,
            "종목코드": self.stock_code,
            "종목명": self.stock_name,
            "주문구분": self.order_side,
            "주문수량": self.order_qty,
            "주문가격": self.order_price,
            "체결수량": self.executed_qty,
            "체결가격": self.executed_price,
            "주문시각": self.order_time,
            "상태": self.status,
        }
