"""
Trading Engine - 자동매매 엔진
"""
import threading
import time
import logging
from datetime import datetime
from typing import Dict, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum

from .config_parser import TradingConfig, StockConfig
from ..factory import KISClient
from ..domain.models import OrderResult

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class EngineStatus(Enum):
    """엔진 상태"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


@dataclass
class TradeLog:
    """거래 로그"""
    timestamp: datetime
    stock_code: str
    stock_name: str
    action: str  # "buy" or "sell"
    quantity: int
    price: int
    success: bool
    message: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "action": self.action,
            "quantity": self.quantity,
            "price": self.price,
            "success": self.success,
            "message": self.message,
        }


@dataclass
class StockStatus:
    """종목별 상태"""
    code: str
    name: str
    current_price: int = 0
    holding_qty: int = 0
    avg_buy_price: int = 0
    eval_amount: int = 0
    profit_rate: float = 0.0
    last_check: Optional[datetime] = None


class TradingEngine:
    """자동매매 엔진"""

    def __init__(
        self,
        client: KISClient,
        config: TradingConfig,
        config_path: Optional[str] = None,
    ):
        self._client = client
        self._config = config
        self._config_path = config_path

        self._status = EngineStatus.STOPPED
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        self._trade_logs: List[TradeLog] = []
        self._stock_status: Dict[str, StockStatus] = {}
        self._daily_trade_count = 0
        self._last_trade_date: Optional[str] = None

        self._callbacks: List[Callable[[TradeLog], None]] = []

    @property
    def status(self) -> EngineStatus:
        return self._status

    @property
    def config(self) -> TradingConfig:
        return self._config

    @property
    def trade_logs(self) -> List[TradeLog]:
        return self._trade_logs.copy()

    @property
    def stock_status(self) -> Dict[str, StockStatus]:
        return self._stock_status.copy()

    def add_callback(self, callback: Callable[[TradeLog], None]) -> None:
        """거래 발생 시 호출될 콜백 등록"""
        self._callbacks.append(callback)

    def reload_config(self, config: Optional[TradingConfig] = None) -> None:
        """설정 리로드"""
        if config:
            self._config = config
        elif self._config_path:
            self._config = TradingConfig.from_file(self._config_path)
        logger.info("Configuration reloaded")

    def save_config(self) -> None:
        """설정 저장"""
        if self._config_path:
            self._config.save_to_file(self._config_path)
            logger.info(f"Configuration saved to {self._config_path}")

    def start(self) -> bool:
        """엔진 시작"""
        if self._status == EngineStatus.RUNNING:
            logger.warning("Engine is already running")
            return False

        if not self._client.is_authenticated:
            if not self._client.authenticate():
                logger.error("Authentication failed")
                return False

        self._stop_event.clear()
        self._status = EngineStatus.RUNNING
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info("Trading engine started")
        return True

    def stop(self) -> None:
        """엔진 정지"""
        if self._status == EngineStatus.STOPPED:
            return

        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        self._status = EngineStatus.STOPPED
        logger.info("Trading engine stopped")

    def pause(self) -> None:
        """엔진 일시정지"""
        if self._status == EngineStatus.RUNNING:
            self._status = EngineStatus.PAUSED
            logger.info("Trading engine paused")

    def resume(self) -> None:
        """엔진 재개"""
        if self._status == EngineStatus.PAUSED:
            self._status = EngineStatus.RUNNING
            logger.info("Trading engine resumed")

    def _run_loop(self) -> None:
        """메인 실행 루프"""
        last_check_times: Dict[str, float] = {}

        while not self._stop_event.is_set():
            if self._status != EngineStatus.RUNNING:
                time.sleep(1)
                continue

            # 일일 거래 횟수 초기화
            self._reset_daily_count_if_needed()

            # 활성화된 종목 처리
            for stock_config in self._config.get_enabled_stocks():
                code = stock_config.code
                interval = self._config.get_interval(stock_config)

                # 모니터링 주기 체크
                last_check = last_check_times.get(code, 0)
                if time.time() - last_check < interval:
                    continue

                last_check_times[code] = time.time()

                try:
                    self._process_stock(stock_config)
                except Exception as e:
                    logger.error(f"Error processing {code}: {e}")

            time.sleep(1)

    def _reset_daily_count_if_needed(self) -> None:
        """일일 거래 횟수 초기화 (날짜 변경 시)"""
        today = datetime.now().strftime("%Y%m%d")
        if self._last_trade_date != today:
            self._daily_trade_count = 0
            self._last_trade_date = today

    def _process_stock(self, stock_config: StockConfig) -> None:
        """개별 종목 처리"""
        code = stock_config.code
        name = stock_config.name

        # 현재가 조회
        price_info = self._client.stock.get_price(code)
        if not price_info:
            logger.warning(f"Failed to get price for {name}({code})")
            return

        current_price = price_info.current_price

        # 보유 수량 조회
        holding_qty = 0
        avg_buy_price = 0
        balance = self._client.account.get_balance()
        if balance:
            for h in balance.holdings:
                if h.stock_code == code:
                    holding_qty = h.quantity
                    avg_buy_price = h.avg_buy_price
                    break

        # 상태 업데이트
        self._stock_status[code] = StockStatus(
            code=code,
            name=name,
            current_price=current_price,
            holding_qty=holding_qty,
            avg_buy_price=avg_buy_price,
            eval_amount=current_price * holding_qty,
            profit_rate=((current_price - avg_buy_price) / avg_buy_price * 100) if avg_buy_price > 0 else 0,
            last_check=datetime.now(),
        )

        logger.info(f"[{name}] 현재가: {current_price:,}원, 보유: {holding_qty}주")

        # 일일 거래 제한 체크
        if self._daily_trade_count >= self._config.max_daily_trades:
            logger.info("Daily trade limit reached")
            return

        # 매도 조건 체크 (보유 중이고 매도가 이상)
        if holding_qty > 0 and current_price >= stock_config.sell_price:
            self._execute_sell(stock_config, holding_qty, current_price)
            return

        # 매수 조건 체크 (매수가 이하)
        if current_price <= stock_config.buy_price:
            self._execute_buy(stock_config, current_price)

    def _execute_buy(self, stock_config: StockConfig, current_price: int) -> None:
        """매수 실행"""
        # 주문 가능 금액 조회
        deposit = self._client.account.get_available_deposit()
        if not deposit:
            logger.warning("Failed to get available deposit")
            return

        available = deposit.available_cash

        # 매수 가능 수량 계산
        max_qty_by_amount = stock_config.max_amount // current_price
        max_qty_by_deposit = available // current_price

        quantity = min(max_qty_by_amount, max_qty_by_deposit)

        if quantity <= 0:
            logger.info(f"[{stock_config.name}] 매수 가능 수량 없음")
            return

        # 매수 주문
        logger.info(f"[{stock_config.name}] 매수 주문: {quantity}주 @ {current_price:,}원")
        result = self._client.order.buy(stock_config.code, quantity, current_price)

        self._log_trade(stock_config, "buy", quantity, current_price, result)

    def _execute_sell(self, stock_config: StockConfig, quantity: int, current_price: int) -> None:
        """매도 실행"""
        logger.info(f"[{stock_config.name}] 매도 주문: {quantity}주 @ {current_price:,}원")
        result = self._client.order.sell(stock_config.code, quantity, current_price)

        self._log_trade(stock_config, "sell", quantity, current_price, result)

    def _log_trade(
        self,
        stock_config: StockConfig,
        action: str,
        quantity: int,
        price: int,
        result: OrderResult,
    ) -> None:
        """거래 로그 기록"""
        log = TradeLog(
            timestamp=datetime.now(),
            stock_code=stock_config.code,
            stock_name=stock_config.name,
            action=action,
            quantity=quantity,
            price=price,
            success=result.success,
            message=result.message,
        )

        self._trade_logs.append(log)
        if result.success:
            self._daily_trade_count += 1

        # 콜백 호출
        for callback in self._callbacks:
            try:
                callback(log)
            except Exception as e:
                logger.error(f"Callback error: {e}")

        if result.success:
            logger.info(f"[{stock_config.name}] {action} 성공: 주문번호 {result.order_no}")
        else:
            logger.warning(f"[{stock_config.name}] {action} 실패: {result.message}")

    def get_summary(self) -> dict:
        """엔진 상태 요약"""
        return {
            "status": self._status.value,
            "daily_trade_count": self._daily_trade_count,
            "max_daily_trades": self._config.max_daily_trades,
            "enabled_stocks": len(self._config.get_enabled_stocks()),
            "total_stocks": len(self._config.stocks),
            "trade_logs_count": len(self._trade_logs),
        }
