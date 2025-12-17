"""
RPC Handler - JSON-RPC 메서드 핸들러
"""
import logging
import os
from typing import Any, Dict, Optional

from ..factory import KISClient
from ..engine.config_parser import TradingConfig, StockConfig, VolatilityBreakoutParams
from ..engine.trading_engine import TradingEngine, EngineStatus
from ..backtest.engine import BacktestEngine
from ..backtest.data_provider import (
    HistoricalDataProvider,
    MockHistoricalDataProvider,
    generate_sample_data,
    generate_minute_sample_data,
)

logger = logging.getLogger(__name__)


def get_config_path() -> str:
    """설정 파일 경로 반환 (production/dev 환경 지원)"""
    config_dir = os.environ.get('AUTOSTOCK_CONFIG_DIR', 'config')
    return os.path.join(config_dir, 'trading_config.yaml')


class RpcHandler:
    """RPC 메서드 핸들러"""

    def __init__(self):
        self._engine: Optional[TradingEngine] = None
        self._client: Optional[KISClient] = None
        self._config_path = get_config_path()

    def _get_engine(self) -> TradingEngine:
        """엔진 인스턴스 반환 (지연 초기화)"""
        if self._engine is None:
            self._client = KISClient()
            config = TradingConfig.from_file(self._config_path)
            self._engine = TradingEngine(self._client, config, self._config_path)
        return self._engine

    def call(self, method: str, params: Dict[str, Any]) -> Any:
        """메서드 호출"""
        # 메서드 라우팅
        method_map = {
            'ping': self.ping,
            'engine.start': self.engine_start,
            'engine.stop': self.engine_stop,
            'engine.pause': self.engine_pause,
            'engine.resume': self.engine_resume,
            'engine.status': self.engine_status,
            'stocks.list': self.stocks_list,
            'stocks.add': self.stocks_add,
            'stocks.update': self.stocks_update,
            'stocks.delete': self.stocks_delete,
            'stocks.toggle': self.stocks_toggle,
            'logs.get': self.logs_get,
            'backtest.run': self.backtest_run,
            'config.get': self.config_get,
            'config.save': self.config_save,
            'config.reload': self.config_reload,
        }

        handler = method_map.get(method)
        if handler is None:
            raise ValueError(f"Unknown method: {method}")

        return handler(params)

    # ============ 기본 ============

    def ping(self, params: Dict) -> Dict:
        """헬스 체크"""
        return {'status': 'ok', 'message': 'pong'}

    # ============ 엔진 ============

    def engine_start(self, params: Dict) -> Dict:
        """엔진 시작"""
        engine = self._get_engine()

        if not self._client or not self._client.is_authenticated:
            if not self._client.authenticate():
                return {'success': False, 'message': 'Authentication failed'}

        engine.start()
        return {'success': True, 'status': engine.status.value}

    def engine_stop(self, params: Dict) -> Dict:
        """엔진 정지"""
        engine = self._get_engine()
        engine.stop()
        return {'success': True, 'status': engine.status.value}

    def engine_pause(self, params: Dict) -> Dict:
        """엔진 일시정지"""
        engine = self._get_engine()
        engine.pause()
        return {'success': True, 'status': engine.status.value}

    def engine_resume(self, params: Dict) -> Dict:
        """엔진 재개"""
        engine = self._get_engine()
        engine.resume()
        return {'success': True, 'status': engine.status.value}

    def engine_status(self, params: Dict) -> Dict:
        """엔진 상태 조회"""
        engine = self._get_engine()
        summary = engine.get_summary()
        return {
            'status': summary['status'],
            'daily_trades': summary.get('daily_trade_count', 0),
            'max_daily_trades': summary.get('max_daily_trades', 10),
            'interval': engine.config.default_interval,
            'enabled_stocks': summary.get('enabled_stocks', 0),
            'total_stocks': summary.get('total_stocks', 0),
            'recent_trades': [
                {
                    'timestamp': log.timestamp,
                    'stock_code': log.stock_code,
                    'stock_name': log.stock_name,
                    'action': log.action,
                    'price': log.price,
                    'quantity': log.quantity,
                    'reason': log.reason,
                }
                for log in engine.trade_logs[-10:]
            ],
        }

    # ============ 종목 ============

    def stocks_list(self, params: Dict) -> Dict:
        """종목 목록 조회"""
        engine = self._get_engine()
        stocks = engine.config.stocks

        return {
            'stocks': [
                {
                    'code': s.code,
                    'name': s.name,
                    'strategy': s.strategy,
                    'max_amount': s.max_amount,
                    'buy_price': s.buy_price,
                    'sell_price': s.sell_price,
                    'enabled': s.enabled,
                    'priority': s.priority,
                    'vb_params': s.vb_params.to_dict() if s.vb_params else None,
                }
                for s in stocks
            ]
        }

    def stocks_add(self, params: Dict) -> Dict:
        """종목 추가"""
        engine = self._get_engine()

        vb_params = None
        if params.get('strategy') == 'volatility_breakout':
            vb_params = VolatilityBreakoutParams(
                k=params.get('k', 0.5),
                target_profit_rate=params.get('target_profit_rate', 2.0),
                stop_loss_rate=params.get('stop_loss_rate', -2.0),
                sell_at_close=params.get('sell_at_close', True),
            )

        strategy = params.get('strategy', 'range_trading')

        stock = StockConfig(
            code=params['code'],
            name=params.get('name', params['code']),
            strategy=strategy,
            max_amount=params.get('max_amount', 1000000),
            buy_price=params.get('buy_price', 0),
            sell_price=params.get('sell_price', 0),
            enabled=params.get('enabled', True),
            priority=params.get('priority', 100),
            vb_params=vb_params,
        )

        engine.config.add_stock(stock)
        engine.config.save_to_file(self._config_path)

        return {'success': True, 'message': f'Stock {params["code"]} added'}

    def stocks_update(self, params: Dict) -> Dict:
        """종목 수정"""
        code = params.get('code')
        if not code:
            raise ValueError("Stock code is required")

        engine = self._get_engine()
        stock = engine.config.get_stock_by_code(code)

        if not stock:
            raise ValueError(f"Stock not found: {code}")

        # 업데이트 가능한 필드
        if 'enabled' in params:
            engine.config.update_stock_enabled(code, params['enabled'])
        if 'priority' in params:
            engine.config.update_stock_priority(code, params['priority'])

        engine.config.save_to_file(self._config_path)
        return {'success': True, 'message': f'Stock {code} updated'}

    def stocks_delete(self, params: Dict) -> Dict:
        """종목 삭제"""
        code = params.get('code')
        if not code:
            raise ValueError("Stock code is required")

        engine = self._get_engine()
        result = engine.config.remove_stock(code)

        if result:
            engine.config.save_to_file(self._config_path)
            return {'success': True, 'message': f'Stock {code} deleted'}
        else:
            raise ValueError(f"Stock not found: {code}")

    def stocks_toggle(self, params: Dict) -> Dict:
        """종목 활성화 토글"""
        code = params.get('code')
        if not code:
            raise ValueError("Stock code is required")

        engine = self._get_engine()
        stock = engine.config.get_stock_by_code(code)

        if not stock:
            raise ValueError(f"Stock not found: {code}")

        new_state = not stock.enabled
        engine.config.update_stock_enabled(code, new_state)
        engine.config.save_to_file(self._config_path)

        return {'success': True, 'enabled': new_state}

    # ============ 로그 ============

    def logs_get(self, params: Dict) -> Dict:
        """거래 로그 조회"""
        limit = params.get('limit', 100)
        engine = self._get_engine()

        logs = engine.trade_logs[-limit:] if limit > 0 else engine.trade_logs

        return {
            'logs': [
                {
                    'timestamp': log.timestamp,
                    'stock_code': log.stock_code,
                    'stock_name': log.stock_name,
                    'action': log.action,
                    'price': log.price,
                    'quantity': log.quantity,
                    'amount': log.amount,
                    'reason': log.reason,
                }
                for log in reversed(logs)
            ]
        }

    # ============ 백테스트 ============

    def backtest_run(self, params: Dict) -> Dict:
        """백테스트 실행"""
        # 전략 파라미터
        strategy = params.get('strategy', 'range_trading')

        if strategy == 'range_trading':
            strategy_params = {
                'buy_price': params.get('buy_price', 0),
                'sell_price': params.get('sell_price', 0),
            }
        else:
            strategy_params = {
                'k': params.get('k', 0.5),
                'target_profit_rate': params.get('target_profit_rate', 2.0),
                'stop_loss_rate': params.get('stop_loss_rate', -2.0),
                'sell_at_close': params.get('sell_at_close', True),
            }

        # 데이터 제공자 설정
        use_mock = params.get('use_mock', True)
        use_minute_data = params.get('use_minute_data', False)

        if use_mock:
            base_price = params.get('buy_price') or 50000
            daily_data = generate_sample_data(
                params['start_date'],
                params['end_date'],
                base_price=base_price,
            )
            minute_data = None
            if use_minute_data:
                minute_data = generate_minute_sample_data(
                    params['start_date'],
                    params['end_date'],
                    base_price=base_price,
                )
            data_provider = MockHistoricalDataProvider(
                daily_data=daily_data,
                minute_data=minute_data,
            )
        else:
            if not self._client or not self._client.is_authenticated:
                self._client = KISClient()
                if not self._client.authenticate():
                    return {'success': False, 'message': 'API 인증 실패'}
            data_provider = HistoricalDataProvider(self._client.stock)

        # 백테스트 실행
        engine = BacktestEngine(data_provider)
        result = engine.run(
            stock_code=params['stock_code'],
            start_date=params['start_date'],
            end_date=params['end_date'],
            initial_capital=params.get('capital', 1000000),
            strategy=strategy,
            strategy_params=strategy_params,
            stock_name=params.get('stock_name', params['stock_code']),
            use_minute_data=use_minute_data,
        )

        # 가격 데이터
        price_data = []
        if use_minute_data and result.minute_prices:
            for mp in result.minute_prices:
                price_data.append({
                    'datetime': mp.datetime,
                    'date': mp.date,
                    'time': mp.time_formatted,
                    'open_price': mp.open_price,
                    'high_price': mp.high_price,
                    'low_price': mp.low_price,
                    'close_price': mp.close_price,
                    'volume': mp.volume,
                })
        else:
            daily_prices = data_provider.get_daily_data(
                params['stock_code'],
                params['start_date'],
                params['end_date'],
            )
            for dp in daily_prices:
                price_data.append({
                    'datetime': dp.date,
                    'date': dp.date,
                    'time': '',
                    'open_price': dp.open_price,
                    'high_price': dp.high_price,
                    'low_price': dp.low_price,
                    'close_price': dp.close_price,
                    'volume': dp.volume,
                })

        # 거래 내역
        trades_data = [
            {
                'date': t.date,
                'trade_type': t.trade_type.value,
                'price': t.price,
                'quantity': t.quantity,
                'amount': t.amount,
                'profit_loss': t.profit_loss,
                'profit_rate': t.profit_rate,
                'reason': t.reason,
            }
            for t in result.trades
        ]

        return {
            'success': True,
            'data': {
                'stock_code': result.stock_code,
                'stock_name': result.stock_name,
                'start_date': result.start_date,
                'end_date': result.end_date,
                'strategy': result.strategy,
                'initial_capital': result.initial_capital,
                'final_capital': result.final_capital,
                'total_trades': result.total_trades,
                'winning_trades': result.winning_trades,
                'losing_trades': result.losing_trades,
                'total_profit_loss': result.total_profit_loss,
                'total_return_rate': result.total_return_rate,
                'max_drawdown': result.max_drawdown,
                'win_rate': result.win_rate,
                'strategy_params': result.strategy_params,
                'trades': trades_data,
                'price_data': price_data,
                'use_minute_data': use_minute_data,
            },
        }

    # ============ 설정 ============

    def config_get(self, params: Dict) -> Dict:
        """설정 조회"""
        engine = self._get_engine()
        return {
            'settings': {
                'default_interval': engine.config.default_interval,
                'max_daily_trades': engine.config.max_daily_trades,
            },
            'stocks': [
                {
                    'code': s.code,
                    'name': s.name,
                    'strategy': s.strategy,
                    'max_amount': s.max_amount,
                    'buy_price': s.buy_price,
                    'sell_price': s.sell_price,
                    'enabled': s.enabled,
                    'priority': s.priority,
                }
                for s in engine.config.stocks
            ],
        }

    def config_save(self, params: Dict) -> Dict:
        """설정 저장"""
        engine = self._get_engine()
        engine.config.save_to_file(self._config_path)
        return {'success': True, 'message': 'Configuration saved'}

    def config_reload(self, params: Dict) -> Dict:
        """설정 다시 로드"""
        engine = self._get_engine()
        engine.reload_config()
        return {'success': True, 'message': 'Configuration reloaded'}
