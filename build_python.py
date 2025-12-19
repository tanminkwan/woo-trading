"""
Python 백엔드 빌드 스크립트 (PyInstaller)
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def build():
    """PyInstaller로 Python 백엔드 빌드"""
    root_dir = Path(__file__).parent
    dist_dir = root_dir / "dist-python"

    # 기존 빌드 삭제
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    # PyInstaller 실행
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "backend",
        "--onefile",
        "--console",  # IPC용 콘솔 앱
        "--distpath", str(dist_dir),
        "--workpath", str(root_dir / "build"),
        "--specpath", str(root_dir / "build"),
        # 모듈 포함
        "--hidden-import", "src",
        "--hidden-import", "src.ipc",
        "--hidden-import", "src.ipc.main",
        "--hidden-import", "src.ipc.handler",
        "--hidden-import", "src.factory",
        "--hidden-import", "src.engine",
        "--hidden-import", "src.engine.config_parser",
        "--hidden-import", "src.engine.trading_engine",
        "--hidden-import", "src.backtest",
        "--hidden-import", "src.backtest.engine",
        "--hidden-import", "src.backtest.data_provider",
        "--hidden-import", "src.services",
        "--hidden-import", "yaml",
        # 데이터 파일 포함
        "--add-data", f"{root_dir / 'config'}:config",
        # 엔트리포인트
        str(root_dir / "src" / "ipc" / "main.py"),
    ]

    print("Building Python backend...")
    print(f"Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, cwd=str(root_dir))

    if result.returncode == 0:
        print(f"\nBuild successful! Output: {dist_dir / 'backend.exe'}")
    else:
        print(f"\nBuild failed with code {result.returncode}")
        sys.exit(1)


if __name__ == "__main__":
    build()
