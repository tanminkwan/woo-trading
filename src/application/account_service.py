"""
Account Service - 계좌 조회 서비스 (SRP, OCP 준수)
"""
from typing import Optional

from ..domain.interfaces import IAccountService, IAuthProvider, IHttpClient
from ..domain.models import Balance, Holdings, AccountSummary, Deposit
from ..infrastructure.config import Config


class KISAccountService(IAccountService):
    """한국투자증권 계좌 서비스"""

    BALANCE_ENDPOINT = "/uapi/domestic-stock/v1/trading/inquire-balance"
    DEPOSIT_ENDPOINT = "/uapi/domestic-stock/v1/trading/inquire-psbl-order"

    def __init__(
        self,
        config: Config,
        auth_provider: IAuthProvider,
        http_client: IHttpClient,
    ):
        self._config = config
        self._auth = auth_provider
        self._http = http_client

    def get_balance(self) -> Optional[Balance]:
        """잔고 조회"""
        url = f"{self._config.base_url}{self.BALANCE_ENDPOINT}"

        headers = self._auth.get_headers()
        headers["tr_id"] = self._config.get_tr_id("balance")

        params = {
            "CANO": self._config.account_prefix,
            "ACNT_PRDT_CD": self._config.account_suffix,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        try:
            response = self._http.get(url, headers=headers, params=params)

            if response.get("rt_cd") == "0":
                # 보유종목 파싱
                holdings = []
                for item in response["output1"]:
                    qty = int(item.get("hldg_qty", 0) or 0)
                    if qty > 0:
                        holdings.append(
                            Holdings(
                                stock_code=item["pdno"],
                                stock_name=item["prdt_name"],
                                quantity=qty,
                                avg_buy_price=int(float(item.get("pchs_avg_pric", 0) or 0)),
                                current_price=int(item.get("prpr", 0) or 0),
                                eval_amount=int(item.get("evlu_amt", 0) or 0),
                                profit_loss=int(item.get("evlu_pfls_amt", 0) or 0),
                                profit_rate=float(item.get("evlu_pfls_rt", 0) or 0),
                            )
                        )

                # 계좌 요약 파싱
                output2 = response["output2"][0] if response.get("output2") else {}
                summary = AccountSummary(
                    deposit=int(output2.get("dnca_tot_amt", 0) or 0),
                    total_buy_amount=int(output2.get("pchs_amt_smtl_amt", 0) or 0),
                    total_eval_amount=int(output2.get("evlu_amt_smtl_amt", 0) or 0),
                    total_profit_loss=int(output2.get("evlu_pfls_smtl_amt", 0) or 0),
                )

                return Balance(holdings=holdings, summary=summary)
            return None
        except Exception:
            return None

    def get_available_deposit(self) -> Optional[Deposit]:
        """주문 가능 금액 조회"""
        url = f"{self._config.base_url}{self.DEPOSIT_ENDPOINT}"

        headers = self._auth.get_headers()
        headers["tr_id"] = self._config.get_tr_id("deposit")

        params = {
            "CANO": self._config.account_prefix,
            "ACNT_PRDT_CD": self._config.account_suffix,
            "PDNO": "005930",  # 임의 종목코드
            "ORD_UNPR": "0",
            "ORD_DVSN": "01",
            "CMA_EVLU_AMT_ICLD_YN": "Y",
            "OVRS_ICLD_YN": "N",
        }

        try:
            response = self._http.get(url, headers=headers, params=params)

            if response.get("rt_cd") == "0":
                output = response["output"]
                return Deposit(
                    available_cash=int(output.get("ord_psbl_cash", 0) or 0),
                    available_total=int(output.get("nrcvb_buy_amt", 0) or 0),
                )
            return None
        except Exception:
            return None
