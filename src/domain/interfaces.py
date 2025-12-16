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


# ============ Backtest Interfaces ============

class IHistoricalDataProvider(ABC):
    """과거 데이터 제공자 인터페이스 (ISP 준수)"""

    @abstractmethod
    def get_daily_data(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
    ) -> List[DailyPrice]:
        """일별 시세 데이터 조회

        Args:
            stock_code: 종목코드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)

        Returns:
            일별 시세 리스트 (날짜 오름차순)
        """
        pass


class IBacktestStrategy(ABC):
    """백테스트 전략 인터페이스 (OCP 준수 - 새 전략 추가 시 기존 코드 수정 불필요)"""

    @abstractmethod
    def should_buy(
        self,
        current_price: int,
        daily_data: DailyPrice,
        prev_data: Optional[DailyPrice],
        position: int,
        params: dict,
    ) -> bool:
        """매수 조건 확인

        Args:
            current_price: 현재가 (시뮬레이션)
            daily_data: 당일 데이터
            prev_data: 전일 데이터
            position: 현재 보유 수량
            params: 전략별 파라미터

        Returns:
            매수 여부
        """
        pass

    @abstractmethod
    def should_sell(
        self,
        current_price: int,
        daily_data: DailyPrice,
        buy_price: int,
        position: int,
        params: dict,
    ) -> bool:
        """매도 조건 확인

        Args:
            current_price: 현재가 (시뮬레이션)
            daily_data: 당일 데이터
            buy_price: 매수 평균가
            position: 현재 보유 수량
            params: 전략별 파라미터

        Returns:
            매도 여부
        """
        pass

    @abstractmethod
    def get_buy_price(
        self,
        daily_data: DailyPrice,
        prev_data: Optional[DailyPrice],
        params: dict,
    ) -> int:
        """매수가 계산

        Args:
            daily_data: 당일 데이터
            prev_data: 전일 데이터
            params: 전략별 파라미터

        Returns:
            매수 예상가
        """
        pass


class IBacktestEngine(ABC):
    """백테스트 엔진 인터페이스 (DIP 준수)"""

    @abstractmethod
    def run(
        self,
        stock_code: str,
        start_date: str,
        end_date: str,
        initial_capital: int,
        strategy: str,
        strategy_params: dict,
    ) -> "BacktestResult":
        """백테스트 실행

        Args:
            stock_code: 종목코드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)
            initial_capital: 초기 자본금
            strategy: 전략 종류 (range_trading, volatility_breakout)
            strategy_params: 전략 파라미터

        Returns:
            백테스트 결과
        """
        pass


# Forward reference for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..backtest.models import BacktestResult
