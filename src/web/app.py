"""
Web Application - FastAPI 기반 웹 서버
"""
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional
import logging

from ..factory import KISClient
from ..engine.config_parser import TradingConfig, StockConfig
from ..engine.trading_engine import TradingEngine, EngineStatus

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
        buy_price: int = Form(...),
        sell_price: int = Form(...),
        interval: Optional[int] = Form(None),
        enabled: bool = Form(True),
    ):
        """종목 추가 API"""
        engine = get_engine()
        stock = StockConfig(
            code=code,
            name=name,
            max_amount=max_amount,
            buy_price=buy_price,
            sell_price=sell_price,
            interval=interval,
            enabled=enabled,
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

    return app
