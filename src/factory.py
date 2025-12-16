"""
Factory Module - 의존성 주입 및 객체 생성 (DIP 준수)
"""
from typing import Optional

from .domain.interfaces import IStockService, IAccountService, IOrderService
from .infrastructure.config import Config
from .infrastructure.http_client import RequestsHttpClient
from .infrastructure.auth import KISAuthProvider
from .application.stock_service import KISStockService
from .application.account_service import KISAccountService
from .application.order_service import KISOrderService


class KISClientFactory:
    """한국투자증권 클라이언트 팩토리"""

    def __init__(self, config: Optional[Config] = None):
        """
        팩토리 초기화

        Args:
            config: 설정 객체 (None이면 환경변수에서 로드)
        """
        self._config = config or Config.from_env()
        self._http_client = RequestsHttpClient()
        self._auth_provider = KISAuthProvider(self._config, self._http_client)

    @property
    def config(self) -> Config:
        return self._config

    @property
    def auth_provider(self) -> KISAuthProvider:
        return self._auth_provider

    def create_stock_service(self) -> IStockService:
        """주식 시세 서비스 생성"""
        return KISStockService(
            config=self._config,
            auth_provider=self._auth_provider,
            http_client=self._http_client,
        )

    def create_account_service(self) -> IAccountService:
        """계좌 서비스 생성"""
        return KISAccountService(
            config=self._config,
            auth_provider=self._auth_provider,
            http_client=self._http_client,
        )

    def create_order_service(self) -> IOrderService:
        """주문 서비스 생성"""
        return KISOrderService(
            config=self._config,
            auth_provider=self._auth_provider,
            http_client=self._http_client,
        )


class KISClient:
    """한국투자증권 통합 클라이언트"""

    def __init__(self, config: Optional[Config] = None):
        """
        클라이언트 초기화

        Args:
            config: 설정 객체 (None이면 환경변수에서 로드)
        """
        factory = KISClientFactory(config)
        self._config = factory.config
        self._auth = factory.auth_provider
        self._stock = factory.create_stock_service()
        self._account = factory.create_account_service()
        self._order = factory.create_order_service()

    @property
    def stock(self) -> IStockService:
        """주식 시세 서비스"""
        return self._stock

    @property
    def account(self) -> IAccountService:
        """계좌 서비스"""
        return self._account

    @property
    def order(self) -> IOrderService:
        """주문 서비스"""
        return self._order

    def authenticate(self) -> bool:
        """인증 수행"""
        try:
            token = self._auth.get_access_token()
            return token is not None
        except Exception:
            return False

    @property
    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        return self._auth.is_authenticated()
