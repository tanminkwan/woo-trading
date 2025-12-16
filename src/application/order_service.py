"""
Order Service - 주문 서비스 (SRP, OCP 준수)
"""
from datetime import datetime
from typing import List, Optional

from ..domain.interfaces import IOrderService, IAuthProvider, IHttpClient
from ..domain.models import OrderResult, OrderInfo, OrderType
from ..infrastructure.config import Config


class KISOrderService(IOrderService):
    """한국투자증권 주문 서비스"""

    ORDER_ENDPOINT = "/uapi/domestic-stock/v1/trading/order-cash"
    ORDERS_ENDPOINT = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"

    def __init__(
        self,
        config: Config,
        auth_provider: IAuthProvider,
        http_client: IHttpClient,
    ):
        self._config = config
        self._auth = auth_provider
        self._http = http_client

    def buy(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: OrderType = OrderType.LIMIT,
    ) -> OrderResult:
        """매수 주문"""
        return self._place_order(
            stock_code=stock_code,
            quantity=quantity,
            price=price,
            order_type=order_type,
            is_buy=True,
        )

    def sell(
        self,
        stock_code: str,
        quantity: int,
        price: int = 0,
        order_type: OrderType = OrderType.LIMIT,
    ) -> OrderResult:
        """매도 주문"""
        return self._place_order(
            stock_code=stock_code,
            quantity=quantity,
            price=price,
            order_type=order_type,
            is_buy=False,
        )

    def _place_order(
        self,
        stock_code: str,
        quantity: int,
        price: int,
        order_type: OrderType,
        is_buy: bool,
    ) -> OrderResult:
        """주문 실행"""
        url = f"{self._config.base_url}{self.ORDER_ENDPOINT}"

        headers = self._auth.get_headers()
        tr_id_key = "buy" if is_buy else "sell"
        headers["tr_id"] = self._config.get_tr_id(tr_id_key)

        # 주문 유형 결정: 가격이 0이면 시장가, 아니면 지정가
        if price > 0:
            ord_dvsn = OrderType.LIMIT.value
        else:
            ord_dvsn = OrderType.MARKET.value

        body = {
            "CANO": self._config.account_prefix,
            "ACNT_PRDT_CD": self._config.account_suffix,
            "PDNO": stock_code,
            "ORD_DVSN": ord_dvsn,
            "ORD_QTY": str(quantity),
            "ORD_UNPR": str(price),
        }

        try:
            response = self._http.post(url, headers=headers, data=body)

            if response.get("rt_cd") == "0":
                output = response["output"]
                return OrderResult(
                    success=True,
                    order_no=output.get("ODNO", ""),
                    order_time=output.get("ORD_TMD", ""),
                    message=response.get("msg1", "주문 성공"),
                )
            else:
                return OrderResult(
                    success=False,
                    message=response.get("msg1", "주문 실패"),
                )
        except Exception as e:
            return OrderResult(
                success=False,
                message=f"주문 실패: {str(e)}",
            )

    def get_orders(self, date: Optional[str] = None) -> Optional[List[OrderInfo]]:
        """주문 내역 조회"""
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        url = f"{self._config.base_url}{self.ORDERS_ENDPOINT}"

        headers = self._auth.get_headers()
        headers["tr_id"] = self._config.get_tr_id("orders")

        params = {
            "CANO": self._config.account_prefix,
            "ACNT_PRDT_CD": self._config.account_suffix,
            "INQR_STRT_DT": date,
            "INQR_END_DT": date,
            "SLL_BUY_DVSN_CD": "00",  # 전체
            "INQR_DVSN": "01",  # 정순
            "PDNO": "",
            "CCLD_DVSN": "00",  # 전체
            "ORD_GNO_BRNO": "",
            "ODNO": "",
            "INQR_DVSN_3": "00",
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        try:
            response = self._http.get(url, headers=headers, params=params)

            if response.get("rt_cd") == "0":
                orders = []
                for item in response.get("output1", []):
                    order_no = item.get("odno", "")
                    if order_no:
                        orders.append(
                            OrderInfo(
                                order_no=order_no,
                                stock_code=item.get("pdno", ""),
                                stock_name=item.get("prdt_name", ""),
                                order_side="매수" if item.get("sll_buy_dvsn_cd") == "02" else "매도",
                                order_qty=int(item.get("ord_qty", 0) or 0),
                                order_price=int(item.get("ord_unpr", 0) or 0),
                                executed_qty=int(item.get("tot_ccld_qty", 0) or 0),
                                executed_price=int(item.get("avg_prvs", 0) or 0),
                                order_time=item.get("ord_tmd", ""),
                            )
                        )
                return orders
            return None
        except Exception:
            return None
