"""
전체 빌드 스크립트
Python 백엔드와 Electron 앱을 함께 빌드
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd, cwd=None, shell=False):
    """명령어 실행"""
    print(f"\n> {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=shell)
    if result.returncode != 0:
        print(f"Command failed with code {result.returncode}")
        sys.exit(1)
    return result


def build_python_backend():
    """Python 백엔드 빌드"""
    print("\n" + "=" * 50)
    print("Building Python Backend...")
    print("=" * 50)

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
        "--console",
        "--distpath", str(dist_dir),
        "--workpath", str(root_dir / "build"),
        "--specpath", str(root_dir / "build"),
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
        str(root_dir / "src" / "ipc" / "main.py"),
    ]

    run_command(cmd, cwd=str(root_dir))
    print(f"Python backend built: {dist_dir / 'backend.exe'}")


def build_electron():
    """Electron 앱 빌드"""
    print("\n" + "=" * 50)
    print("Building Electron App...")
    print("=" * 50)

    root_dir = Path(__file__).parent
    electron_dir = root_dir / "electron"

    # React 빌드
    print("\nBuilding React renderer...")
    run_command(["npm", "run", "build:renderer"], cwd=str(electron_dir), shell=True)

    # Electron 빌드
    print("\nPackaging Electron app...")
    run_command(["npm", "run", "dist:win"], cwd=str(electron_dir), shell=True)

    print(f"\nElectron app built: {electron_dir / 'dist'}")


def main():
    """메인 함수"""
    import argparse
    parser = argparse.ArgumentParser(description="Build AutoStock application")
    parser.add_argument("--python-only", action="store_true", help="Build only Python backend")
    parser.add_argument("--electron-only", action="store_true", help="Build only Electron app")
    args = parser.parse_args()

    print("=" * 50)
    print("AutoStock Build Script")
    print("=" * 50)

    if args.python_only:
        build_python_backend()
    elif args.electron_only:
        build_electron()
    else:
        build_python_backend()
        build_electron()

    print("\n" + "=" * 50)
    print("Build Complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
