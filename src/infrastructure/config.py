"""
Configuration Module - 환경 설정 관리 (SRP 준수)
"""
import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from dotenv import load_dotenv


class Environment(Enum):
    """실행 환경"""
    PRODUCTION = "prod"
    DEVELOPMENT = "dev"


@dataclass
class Config:
    """애플리케이션 설정"""
    app_key: str
    app_secret: str
    account_no: str
    environment: Environment

    # API URL
    _PROD_URL = "https://openapi.koreainvestment.com:9443"
    _DEV_URL = "https://openapivts.koreainvestment.com:29443"

    # Transaction IDs
    TR_IDS = {
        "prod": {
            "price": "FHKST01010100",
            "asking_price": "FHKST01010200",
            "daily_price": "FHKST01010400",
            "minute_price": "FHKST03010200",
            "balance": "TTTC8434R",
            "deposit": "TTTC8908R",
            "buy": "TTTC0802U",
            "sell": "TTTC0801U",
            "orders": "TTTC8001R",
        },
        "dev": {
            "price": "FHKST01010100",
            "asking_price": "FHKST01010200",
            "daily_price": "FHKST01010400",
            "minute_price": "FHKST03010200",
            "balance": "VTTC8434R",
            "deposit": "VTTC8908R",
            "buy": "VTTC0802U",
            "sell": "VTTC0801U",
            "orders": "VTTC8001R",
        },
    }

    @property
    def base_url(self) -> str:
        """환경에 따른 API Base URL 반환"""
        if self.environment == Environment.PRODUCTION:
            return self._PROD_URL
        return self._DEV_URL

    @property
    def account_prefix(self) -> str:
        """계좌번호 앞 8자리"""
        return self.account_no.split("-")[0]

    @property
    def account_suffix(self) -> str:
        """계좌번호 뒤 2자리"""
        return self.account_no.split("-")[1]

    def get_tr_id(self, operation: str) -> str:
        """거래 ID 반환"""
        env_key = "prod" if self.environment == Environment.PRODUCTION else "dev"
        return self.TR_IDS[env_key].get(operation, "")

    @classmethod
    def from_env(cls, env_path: Optional[str] = None) -> "Config":
        """환경 변수에서 설정 로드"""
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

        app_key = os.getenv("APP_KEY", "")
        app_secret = os.getenv("APP_SECRET", "")
        account_no = os.getenv("ACCOUNT_NO", "")
        env_str = os.getenv("ENV", "dev")

        if not app_key or not app_secret:
            raise ValueError("APP_KEY and APP_SECRET must be set")
        if not account_no:
            raise ValueError("ACCOUNT_NO must be set")

        environment = (
            Environment.PRODUCTION
            if env_str == "prod"
            else Environment.DEVELOPMENT
        )

        return cls(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            environment=environment,
        )

    @classmethod
    def create(
        cls,
        app_key: str,
        app_secret: str,
        account_no: str,
        is_production: bool = False,
    ) -> "Config":
        """직접 설정 생성"""
        return cls(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            environment=(
                Environment.PRODUCTION if is_production else Environment.DEVELOPMENT
            ),
        )
