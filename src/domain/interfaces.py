"""
Domain Interfaces - 의존성 역전을 위한 인터페이스 정의 (ISP, DIP 준수)
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

from .models import (
    StockPrice,
    AskingPrice,
    DailyPrice,
    Balance,
    Deposit,
    OrderResult,
    OrderInfo,
    OrderType,
)


class IAuthProvider(ABC):
    """인증 제공자 인터페이스"""

    @abstractmethod
    def get_access_token(self) -> Optional[str]:
        """액세스 토큰 발급"""
        pass

    @abstractmethod
    def get_headers(self) -> Dict[str, str]:
        """인증 헤더 반환"""
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        pass


class IHttpClient(ABC):
    """HTTP 클라이언트 인터페이스"""

    @abstractmethod
    def get(
        self,
        url: str,
        headers: Dict[str, str],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """GET 요청"""
        pass

    @abstractmethod
    def post(
        self,
        url: str,
        headers: Dict[str, str],
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """POST 요청"""
        pass


class IStockService(ABC):
    """주식 시세 서비스 인터페이스"""

    @abstractmethod
    def get_price(self, stock_code: str) -> Optional[StockPrice]:
        """현재가 조회"""
        pass

    @abstractmethod
    def get_asking_price(self, stock_code: str) -> Optional[AskingPrice]:
        """호가 조회"""
        pass

    @abstractmethod
    def get_daily_prices(
        self, stock_code: str, period: str = "D"
    ) -> Optional[List[DailyPrice]]:
        """일별 시세 조회"""
        pass


class IAccountService(ABC):
    """계좌 서비스 인터페이스"""

    @abstractmethod
    def get_balance(self) -> Optional[Balance]:
        """잔고 조회"""
        pass

    @abstractmethod
    def get_available_deposit(self) -> Optional[Deposit]:
        """주문 가능 금액 조회"""
        pass


class IOrderService(ABC):
    """주문 서비스 인터페이스"""

    @abstractmethod
    def buy(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: OrderType = OrderType.LIMIT,
    ) -> OrderResult:
        """매수 주문"""
        pass

    @abstractmethod
    def sell(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: OrderType = OrderType.LIMIT,
    ) -> OrderResult:
        """매도 주문"""
        pass

    @abstractmethod
    def get_orders(self, date: Optional[str] = None) -> Optional[List[OrderInfo]]:
        """주문 내역 조회"""
        pass
