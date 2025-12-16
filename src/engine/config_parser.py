"""
Trading Configuration Parser - YAML 설정 파일 파서
"""
import yaml
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path
from enum import Enum


class TradingStrategy(Enum):
    """거래 전략"""
    RANGE_TRADING = "range_trading"           # 범위 매매 (기존)
    VOLATILITY_BREAKOUT = "volatility_breakout"  # 변동성 돌파


@dataclass
class VolatilityBreakoutParams:
    """변동성 돌파 전략 파라미터"""
    k: float = 0.5                    # 변동성 계수 (0.1 ~ 1.0, 기본 0.5)
    target_profit_rate: float = 2.0  # 목표 수익률 (%), 도달 시 매도
    stop_loss_rate: float = -2.0     # 손절 수익률 (%), 도달 시 매도
    sell_at_close: bool = True       # 장 마감 전 매도 여부

    def to_dict(self) -> Dict[str, Any]:
        return {
            "k": self.k,
            "target_profit_rate": self.target_profit_rate,
            "stop_loss_rate": self.stop_loss_rate,
            "sell_at_close": self.sell_at_close,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VolatilityBreakoutParams":
        if not data:
            return cls()
        return cls(
            k=float(data.get("k", 0.5)),
            target_profit_rate=float(data.get("target_profit_rate", 2.0)),
            stop_loss_rate=float(data.get("stop_loss_rate", -2.0)),
            sell_at_close=bool(data.get("sell_at_close", True)),
        )


@dataclass
class StockConfig:
    """개별 종목 설정"""
    code: str
    name: str
    max_amount: int
    buy_price: int = 0                # range_trading 전용
    sell_price: int = 0               # range_trading 전용
    interval: Optional[int] = None
    enabled: bool = True
    priority: int = 100               # 우선순위 (낮을수록 높은 우선순위)
    strategy: str = "range_trading"   # 전략: range_trading, volatility_breakout
    vb_params: Optional[VolatilityBreakoutParams] = None  # 변동성 돌파 파라미터

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "code": self.code,
            "name": self.name,
            "max_amount": self.max_amount,
            "interval": self.interval,
            "enabled": self.enabled,
            "priority": self.priority,
            "strategy": self.strategy,
        }
        # 전략별 파라미터 추가
        if self.strategy == TradingStrategy.RANGE_TRADING.value:
            result["buy_price"] = self.buy_price
            result["sell_price"] = self.sell_price
        elif self.strategy == TradingStrategy.VOLATILITY_BREAKOUT.value and self.vb_params:
            result["vb_params"] = self.vb_params.to_dict()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StockConfig":
        strategy = str(data.get("strategy", "range_trading"))
        vb_params = None
        if strategy == TradingStrategy.VOLATILITY_BREAKOUT.value:
            vb_params = VolatilityBreakoutParams.from_dict(data.get("vb_params", {}))

        return cls(
            code=str(data.get("code", "")),
            name=str(data.get("name", "")),
            max_amount=int(data.get("max_amount", 0)),
            buy_price=int(data.get("buy_price", 0)),
            sell_price=int(data.get("sell_price", 0)),
            interval=data.get("interval"),
            enabled=bool(data.get("enabled", True)),
            priority=int(data.get("priority", 100)),
            strategy=strategy,
            vb_params=vb_params,
        )


@dataclass
class TradingConfig:
    """전체 거래 설정"""
    default_interval: int = 60
    max_daily_trades: int = 10
    stocks: List[StockConfig] = field(default_factory=list)

    def get_enabled_stocks(self) -> List[StockConfig]:
        """활성화된 종목만 반환 (우선순위 순으로 정렬)"""
        return sorted([s for s in self.stocks if s.enabled], key=lambda x: x.priority)

    def get_stock_by_code(self, code: str) -> Optional[StockConfig]:
        """종목코드로 설정 조회"""
        for stock in self.stocks:
            if stock.code == code:
                return stock
        return None

    def get_interval(self, stock: StockConfig) -> int:
        """종목별 모니터링 주기 반환"""
        return stock.interval if stock.interval else self.default_interval

    def to_dict(self) -> Dict[str, Any]:
        return {
            "settings": {
                "default_interval": self.default_interval,
                "max_daily_trades": self.max_daily_trades,
            },
            "stocks": [s.to_dict() for s in self.stocks],
        }

    def to_yaml(self) -> str:
        """YAML 문자열로 변환"""
        return yaml.dump(self.to_dict(), allow_unicode=True, default_flow_style=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradingConfig":
        settings = data.get("settings", {})
        stocks_data = data.get("stocks", [])

        stocks = [StockConfig.from_dict(s) for s in stocks_data]

        return cls(
            default_interval=int(settings.get("default_interval", 60)),
            max_daily_trades=int(settings.get("max_daily_trades", 10)),
            stocks=stocks,
        )

    @classmethod
    def from_yaml(cls, yaml_content: str) -> "TradingConfig":
        """YAML 문자열에서 로드"""
        data = yaml.safe_load(yaml_content)
        return cls.from_dict(data) if data else cls()

    @classmethod
    def from_file(cls, file_path: str) -> "TradingConfig":
        """YAML 파일에서 로드"""
        path = Path(file_path)
        if not path.exists():
            return cls()

        with open(path, "r", encoding="utf-8") as f:
            return cls.from_yaml(f.read())

    def save_to_file(self, file_path: str) -> None:
        """YAML 파일로 저장"""
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(self.to_yaml())

    def add_stock(self, stock: StockConfig) -> None:
        """종목 추가"""
        # 기존 종목 업데이트 또는 추가
        existing = self.get_stock_by_code(stock.code)
        if existing:
            self.stocks.remove(existing)
        self.stocks.append(stock)

    def remove_stock(self, code: str) -> bool:
        """종목 제거"""
        stock = self.get_stock_by_code(code)
        if stock:
            self.stocks.remove(stock)
            return True
        return False

    def update_stock_enabled(self, code: str, enabled: bool) -> bool:
        """종목 활성화 상태 변경"""
        stock = self.get_stock_by_code(code)
        if stock:
            idx = self.stocks.index(stock)
            self.stocks[idx] = StockConfig(
                code=stock.code,
                name=stock.name,
                max_amount=stock.max_amount,
                buy_price=stock.buy_price,
                sell_price=stock.sell_price,
                interval=stock.interval,
                enabled=enabled,
                priority=stock.priority,
            )
            return True
        return False

    def update_stock_priority(self, code: str, priority: int) -> bool:
        """종목 우선순위 변경"""
        stock = self.get_stock_by_code(code)
        if stock:
            idx = self.stocks.index(stock)
            self.stocks[idx] = StockConfig(
                code=stock.code,
                name=stock.name,
                max_amount=stock.max_amount,
                buy_price=stock.buy_price,
                sell_price=stock.sell_price,
                interval=stock.interval,
                enabled=stock.enabled,
                priority=priority,
            )
            return True
        return False
