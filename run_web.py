#!/usr/bin/env python3
"""
웹 서버 실행 스크립트
"""
import uvicorn
from src.web.app import create_app

app = create_app()

if __name__ == "__main__":
    print("=" * 50)
    print("Auto Trading System - Web Server")
    print("=" * 50)
    print("URL: http://localhost:8000")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    uvicorn.run(
        "run_web:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
