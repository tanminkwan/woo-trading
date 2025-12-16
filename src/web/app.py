"""
Web Application - FastAPI 기반 웹 서버
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pathlib import Path
from typing import Optional
import logging

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

# 전역 변수
_engine: Optional[TradingEngine] = None
_client: Optional[KISClient] = None
_config_path: str = "config/trading_config.yaml"


def get_engine() -> TradingEngine:
    """엔진 인스턴스 반환"""
    global _engine, _client
    if _engine is None:
        _client = KISClient()
        config = TradingConfig.from_file(_config_path)
        _engine = TradingEngine(_client, config, _config_path)
    return _engine


def create_app() -> FastAPI:
    """FastAPI 앱 생성"""
    app = FastAPI(
        title="Auto Trading System",
        description="한국투자증권 자동매매 시스템",
        version="1.0.0",
    )

    # 템플릿 설정
    templates_path = Path(__file__).parent / "templates"
    templates = Jinja2Templates(directory=str(templates_path))

    # 정적 파일 설정
    static_path = Path(__file__).parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    # ============ 페이지 라우트 ============

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """메인 대시보드"""
        engine = get_engine()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "status": engine.status.value,
            "summary": engine.get_summary(),
            "stocks": engine.config.stocks,
            "stock_status": engine.stock_status,
        })

    @app.get("/config", response_class=HTMLResponse)
    async def config_page(request: Request):
        """설정 페이지"""
        engine = get_engine()
        return templates.TemplateResponse("config.html", {
            "request": request,
            "config": engine.config,
            "stocks": engine.config.stocks,
        })

    @app.get("/logs", response_class=HTMLResponse)
    async def logs_page(request: Request):
        """거래 로그 페이지"""
        engine = get_engine()
        return templates.TemplateResponse("logs.html", {
            "request": request,
            "logs": engine.trade_logs[-50:],  # 최근 50개
        })

    @app.get("/backtest", response_class=HTMLResponse)
    async def backtest_page(request: Request):
        """백테스트 페이지"""
        return templates.TemplateResponse("backtest.html", {
            "request": request,
        })

    # ============ API 라우트 ============

    @app.post("/api/engine/start")
    async def api_start_engine():
        """엔진 시작 API"""
        engine = get_engine()
        if engine.start():
            return {"success": True, "message": "Engine started"}
        return {"success": False, "message": "Failed to start engine"}

    @app.post("/api/engine/stop")
    async def api_stop_engine():
        """엔진 정지 API"""
        engine = get_engine()
        engine.stop()
        return {"success": True, "message": "Engine stopped"}

    @app.post("/api/engine/pause")
    async def api_pause_engine():
        """엔진 일시정지 API"""
        engine = get_engine()
        engine.pause()
        return {"success": True, "message": "Engine paused"}

    @app.post("/api/engine/resume")
    async def api_resume_engine():
        """엔진 재개 API"""
        engine = get_engine()
        engine.resume()
        return {"success": True, "message": "Engine resumed"}

    @app.get("/api/engine/status")
    async def api_engine_status():
        """엔진 상태 조회 API"""
        engine = get_engine()
        return {
            "status": engine.status.value,
            "summary": engine.get_summary(),
            "stock_status": {k: {
                "code": v.code,
                "name": v.name,
                "current_price": v.current_price,
                "holding_qty": v.holding_qty,
                "profit_rate": v.profit_rate,
                "last_check": v.last_check.isoformat() if v.last_check else None,
                "target_price": v.target_price,
                "prev_high": v.prev_high,
                "prev_low": v.prev_low,
                "today_open": v.today_open,
                "vb_bought_today": v.vb_bought_today,
            } for k, v in engine.stock_status.items()},
        }

    @app.get("/api/stocks")
    async def api_get_stocks():
        """종목 목록 조회 API"""
        engine = get_engine()
        return {"stocks": [s.to_dict() for s in engine.config.stocks]}

    @app.post("/api/stocks")
    async def api_add_stock(
        code: str = Form(...),
        name: str = Form(...),
        max_amount: int = Form(...),
        strategy: str = Form("range_trading"),
        buy_price: int = Form(0),
        sell_price: int = Form(0),
        interval: Optional[int] = Form(None),
        enabled: bool = Form(True),
        priority: int = Form(100),
        vb_k: float = Form(0.5),
        vb_target: float = Form(2.0),
        vb_stop: float = Form(-2.0),
        vb_close: str = Form("true"),
    ):
        """종목 추가 API"""
        engine = get_engine()

        # 변동성 돌파 파라미터 설정
        vb_params = None
        if strategy == "volatility_breakout":
            vb_params = VolatilityBreakoutParams(
                k=vb_k,
                target_profit_rate=vb_target,
                stop_loss_rate=vb_stop,
                sell_at_close=(vb_close.lower() == "true"),
            )

        stock = StockConfig(
            code=code,
            name=name,
            max_amount=max_amount,
            buy_price=buy_price,
            sell_price=sell_price,
            interval=interval,
            enabled=enabled,
            priority=priority,
            strategy=strategy,
            vb_params=vb_params,
        )
        engine.config.add_stock(stock)
        engine.save_config()
        return RedirectResponse(url="/config", status_code=303)

    @app.post("/api/stocks/{code}/delete")
    async def api_delete_stock(code: str):
        """종목 삭제 API"""
        engine = get_engine()
        if engine.config.remove_stock(code):
            engine.save_config()
            return {"success": True}
        raise HTTPException(status_code=404, detail="Stock not found")

    @app.post("/api/stocks/{code}/toggle")
    async def api_toggle_stock(code: str):
        """종목 활성화/비활성화 토글 API"""
        engine = get_engine()
        stock = engine.config.get_stock_by_code(code)
        if stock:
            engine.config.update_stock_enabled(code, not stock.enabled)
            engine.save_config()
            return {"success": True, "enabled": not stock.enabled}
        raise HTTPException(status_code=404, detail="Stock not found")

    @app.get("/api/logs")
    async def api_get_logs(limit: int = 50):
        """거래 로그 조회 API"""
        engine = get_engine()
        logs = engine.trade_logs[-limit:]
        return {"logs": [log.to_dict() for log in logs]}

    @app.get("/api/account/balance")
    async def api_get_balance():
        """계좌 잔고 조회 API"""
        engine = get_engine()
        if not _client or not _client.is_authenticated:
            if not _client.authenticate():
                raise HTTPException(status_code=401, detail="Authentication failed")

        balance = _client.account.get_balance()
        if balance:
            return {
                "holdings": [h.to_dict() for h in balance.holdings],
                "summary": balance.summary.to_dict(),
            }
        raise HTTPException(status_code=500, detail="Failed to get balance")

    @app.get("/api/account/deposit")
    async def api_get_deposit():
        """주문가능금액 조회 API"""
        engine = get_engine()
        if not _client or not _client.is_authenticated:
            if not _client.authenticate():
                raise HTTPException(status_code=401, detail="Authentication failed")

        deposit = _client.account.get_available_deposit()
        if deposit:
            return deposit.to_dict()
        raise HTTPException(status_code=500, detail="Failed to get deposit")

    @app.post("/api/config/reload")
    async def api_reload_config():
        """설정 리로드 API"""
        engine = get_engine()
        engine.reload_config()
        return {"success": True, "message": "Configuration reloaded"}

    # ============ 백테스트 API ============

    class BacktestRequest(BaseModel):
        """백테스트 요청 모델"""
        stock_code: str
        stock_name: Optional[str] = ""
        start_date: str
        end_date: str
        capital: int = 1000000
        strategy: str = "range_trading"
        use_mock: bool = True
        use_minute_data: bool = False  # 분봉 데이터 사용 여부
        # Range Trading params
        buy_price: Optional[int] = 0
        sell_price: Optional[int] = 0
        # Volatility Breakout params
        k: Optional[float] = 0.5
        target_profit_rate: Optional[float] = 2.0
        stop_loss_rate: Optional[float] = -2.0
        sell_at_close: Optional[bool] = True

    @app.post("/api/backtest/run")
    async def api_run_backtest(request: BacktestRequest):
        """백테스트 실행 API"""
        try:
            # 전략 파라미터 설정
            if request.strategy == "range_trading":
                strategy_params = {
                    "buy_price": request.buy_price or 0,
                    "sell_price": request.sell_price or 0,
                }
            else:  # volatility_breakout
                strategy_params = {
                    "k": request.k or 0.5,
                    "target_profit_rate": request.target_profit_rate or 2.0,
                    "stop_loss_rate": request.stop_loss_rate or -2.0,
                    "sell_at_close": request.sell_at_close if request.sell_at_close is not None else True,
                }

            # 데이터 제공자 설정
            if request.use_mock:
                base_price = request.buy_price if request.buy_price and request.buy_price > 0 else 50000
                daily_data = generate_sample_data(
                    request.start_date,
                    request.end_date,
                    base_price=base_price
                )
                minute_data = None
                if request.use_minute_data:
                    minute_data = generate_minute_sample_data(
                        request.start_date,
                        request.end_date,
                        base_price=base_price
                    )
                data_provider = MockHistoricalDataProvider(
                    daily_data=daily_data,
                    minute_data=minute_data
                )
            else:
                global _client
                if not _client or not _client.is_authenticated:
                    _client = KISClient()
                    if not _client.authenticate():
                        return {"success": False, "message": "API 인증 실패. Mock 데이터를 사용하세요."}
                data_provider = HistoricalDataProvider(_client.stock)

            # 일별 가격 데이터 조회 (차트용)
            daily_prices = data_provider.get_daily_data(
                request.stock_code,
                request.start_date,
                request.end_date
            )

            # 백테스트 실행
            engine = BacktestEngine(data_provider)
            result = engine.run(
                stock_code=request.stock_code,
                start_date=request.start_date,
                end_date=request.end_date,
                initial_capital=request.capital,
                strategy=request.strategy,
                strategy_params=strategy_params,
                stock_name=request.stock_name or request.stock_code,
                use_minute_data=request.use_minute_data,
            )

            # 가격 데이터 변환 (분봉 또는 일봉)
            price_data = []
            if request.use_minute_data and result.minute_prices:
                for mp in result.minute_prices:
                    price_data.append({
                        "datetime": mp.datetime,
                        "date": mp.date,
                        "time": mp.time_formatted,
                        "open_price": mp.open_price,
                        "high_price": mp.high_price,
                        "low_price": mp.low_price,
                        "close_price": mp.close_price,
                        "volume": mp.volume,
                    })
            else:
                for dp in daily_prices:
                    price_data.append({
                        "datetime": dp.date,
                        "date": dp.date,
                        "time": "",
                        "open_price": dp.open_price,
                        "high_price": dp.high_price,
                        "low_price": dp.low_price,
                        "close_price": dp.close_price,
                        "volume": dp.volume,
                    })

            # 결과 변환
            trades_data = []
            for trade in result.trades:
                trades_data.append({
                    "date": trade.date,
                    "trade_type": trade.trade_type.value,
                    "price": trade.price,
                    "quantity": trade.quantity,
                    "amount": trade.amount,
                    "profit_loss": trade.profit_loss,
                    "profit_rate": trade.profit_rate,
                    "reason": trade.reason,
                })

            return {
                "success": True,
                "data": {
                    "stock_code": result.stock_code,
                    "stock_name": result.stock_name,
                    "start_date": result.start_date,
                    "end_date": result.end_date,
                    "strategy": result.strategy,
                    "initial_capital": result.initial_capital,
                    "final_capital": result.final_capital,
                    "total_trades": result.total_trades,
                    "winning_trades": result.winning_trades,
                    "losing_trades": result.losing_trades,
                    "total_profit_loss": result.total_profit_loss,
                    "total_return_rate": result.total_return_rate,
                    "max_drawdown": result.max_drawdown,
                    "win_rate": result.win_rate,
                    "strategy_params": result.strategy_params,
                    "trades": trades_data,
                    "price_data": price_data,
                    "use_minute_data": request.use_minute_data,
                }
            }

        except Exception as e:
            logger.error(f"Backtest error: {e}")
            return {"success": False, "message": str(e)}

    return app
