"""
Stock Service - 주식 시세 조회 서비스 (SRP, OCP 준수)
"""
from typing import List, Optional

from ..domain.interfaces import IStockService, IAuthProvider, IHttpClient
from ..domain.models import StockPrice, AskingPrice, DailyPrice
from ..infrastructure.config import Config


class KISStockService(IStockService):
    """한국투자증권 주식 시세 서비스"""

    # API Endpoints
    PRICE_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-price"
    ASKING_PRICE_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-asking-price-exp-ccn"
    DAILY_PRICE_ENDPOINT = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"

    # Market Division Code
    MARKET_CODE_STOCK = "J"

    def __init__(
        self,
        config: Config,
        auth_provider: IAuthProvider,
        http_client: IHttpClient,
    ):
        self._config = config
        self._auth = auth_provider
        self._http = http_client

    def get_price(self, stock_code: str) -> Optional[StockPrice]:
        """현재가 조회"""
        url = f"{self._config.base_url}{self.PRICE_ENDPOINT}"

        headers = self._auth.get_headers()
        headers["tr_id"] = self._config.get_tr_id("price")

        params = {
            "FID_COND_MRKT_DIV_CODE": self.MARKET_CODE_STOCK,
            "FID_INPUT_ISCD": stock_code,
        }

        try:
            response = self._http.get(url, headers=headers, params=params)

            if response.get("rt_cd") == "0":
                output = response["output"]
                return StockPrice(
                    stock_code=stock_code,
                    current_price=int(output["stck_prpr"]),
                    change_price=int(output["prdy_vrss"]),
                    change_rate=float(output["prdy_ctrt"]),
                    open_price=int(output["stck_oprc"]),
                    high_price=int(output["stck_hgpr"]),
                    low_price=int(output["stck_lwpr"]),
                    volume=int(output["acml_vol"]),
                )
            return None
        except Exception:
            return None

    def get_asking_price(self, stock_code: str) -> Optional[AskingPrice]:
        """호가 조회"""
        url = f"{self._config.base_url}{self.ASKING_PRICE_ENDPOINT}"

        headers = self._auth.get_headers()
        headers["tr_id"] = self._config.get_tr_id("asking_price")

        params = {
            "FID_COND_MRKT_DIV_CODE": self.MARKET_CODE_STOCK,
            "FID_INPUT_ISCD": stock_code,
        }

        try:
            response = self._http.get(url, headers=headers, params=params)

            if response.get("rt_cd") == "0":
                output = response["output1"]
                return AskingPrice(
                    sell_prices=[
                        int(output["askp1"]),
                        int(output["askp2"]),
                        int(output["askp3"]),
                    ],
                    buy_prices=[
                        int(output["bidp1"]),
                        int(output["bidp2"]),
                        int(output["bidp3"]),
                    ],
                    sell_volumes=[
                        int(output["askp_rsqn1"]),
                        int(output["askp_rsqn2"]),
                        int(output["askp_rsqn3"]),
                    ],
                    buy_volumes=[
                        int(output["bidp_rsqn1"]),
                        int(output["bidp_rsqn2"]),
                        int(output["bidp_rsqn3"]),
                    ],
                )
            return None
        except Exception:
            return None

    def get_daily_prices(
        self, stock_code: str, period: str = "D"
    ) -> Optional[List[DailyPrice]]:
        """일별 시세 조회"""
        url = f"{self._config.base_url}{self.DAILY_PRICE_ENDPOINT}"

        headers = self._auth.get_headers()
        headers["tr_id"] = self._config.get_tr_id("daily_price")

        params = {
            "FID_COND_MRKT_DIV_CODE": self.MARKET_CODE_STOCK,
            "FID_INPUT_ISCD": stock_code,
            "FID_PERIOD_DIV_CODE": period,
            "FID_ORG_ADJ_PRC": "0",  # 수정주가
        }

        try:
            response = self._http.get(url, headers=headers, params=params)

            if response.get("rt_cd") == "0":
                result = []
                for item in response["output"]:
                    result.append(
                        DailyPrice(
                            date=item["stck_bsop_date"],
                            close_price=int(item["stck_clpr"]),
                            open_price=int(item["stck_oprc"]),
                            high_price=int(item["stck_hgpr"]),
                            low_price=int(item["stck_lwpr"]),
                            volume=int(item["acml_vol"]),
                        )
                    )
                return result
            return None
        except Exception:
            return None
