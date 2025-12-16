"""
Trading Configuration Parser - YAML 설정 파일 파서
"""
import yaml
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class StockConfig:
    """개별 종목 설정"""
    code: str
    name: str
    max_amount: int
    buy_price: int
    sell_price: int
    interval: Optional[int] = None
    enabled: bool = True
    priority: int = 100  # 우선순위 (낮을수록 높은 우선순위, 기본값 100)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "name": self.name,
            "max_amount": self.max_amount,
            "buy_price": self.buy_price,
            "sell_price": self.sell_price,
            "interval": self.interval,
            "enabled": self.enabled,
            "priority": self.priority,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StockConfig":
        return cls(
            code=str(data.get("code", "")),
            name=str(data.get("name", "")),
            max_amount=int(data.get("max_amount", 0)),
            buy_price=int(data.get("buy_price", 0)),
            sell_price=int(data.get("sell_price", 0)),
            interval=data.get("interval"),
            enabled=bool(data.get("enabled", True)),
            priority=int(data.get("priority", 100)),
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
