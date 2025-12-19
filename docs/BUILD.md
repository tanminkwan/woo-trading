# 빌드 가이드

소스 코드에서 배포 가능한 설치 파일을 생성하는 방법입니다.

## 빌드 환경

### 필수 요구사항

| 요구사항 | 버전 | 확인 명령어 |
|----------|------|-------------|
| Python | 3.10+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |

### 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/your-repo/auto-stock.git
cd auto-stock

# Python 의존성 설치
pip install -r requirements.txt

# PyInstaller 설치 (빌드용)
pip install pyinstaller

# Electron 의존성 설치
cd electron && npm install
cd renderer && npm install
cd ../..
```

## 빌드 방법

### 전체 빌드 (권장)

Python 백엔드와 Electron 앱을 한 번에 빌드합니다.

```bash
python build.py
```

### 개별 빌드

#### Python 백엔드만 빌드

```bash
python build.py --python-only
```

출력: `dist-python/backend.exe` (약 55MB)

#### Electron 앱만 빌드

```bash
python build.py --electron-only

# 또는 직접 실행
cd electron && npm run dist:win
```

출력: `electron/dist/AutoStock Setup 1.0.0.exe` (약 130MB)

## 빌드 결과물

```
auto-stock/
├── dist-python/
│   └── backend.exe              # Python 백엔드 실행파일
│
└── electron/dist/
    ├── AutoStock Setup 1.0.0.exe    # Windows 설치파일 (배포용)
    ├── AutoStock Setup 1.0.0.exe.blockmap
    └── win-unpacked/                # 압축 해제된 앱 (테스트용)
        └── AutoStock.exe
```

## 빌드 스크립트 상세

### build.py 옵션

| 옵션 | 설명 |
|------|------|
| (없음) | 전체 빌드 (Python + Electron) |
| `--python-only` | Python 백엔드만 빌드 |
| `--electron-only` | Electron 앱만 빌드 |

### PyInstaller 설정

`build.py`에서 사용하는 PyInstaller 옵션:

```python
cmd = [
    "python", "-m", "PyInstaller",
    "--name", "backend",        # 출력 파일명
    "--onefile",                # 단일 실행파일
    "--console",                # 콘솔 앱 (GUI 없음)
    "--distpath", "dist-python",
    "--hidden-import", "src",   # 숨겨진 의존성
    "--hidden-import", "yaml",
    "backend_entry.py",         # 엔트리포인트
]
```

### Electron Builder 설정

`electron/package.json`의 빌드 설정:

```json
{
  "build": {
    "appId": "com.autostock.app",
    "productName": "AutoStock",
    "win": {
      "target": "nsis"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true
    },
    "extraResources": [
      {
        "from": "../dist-python/backend.exe",
        "to": "python-backend/backend.exe"
      },
      {
        "from": "../config",
        "to": "config"
      }
    ]
  }
}
```

## 개발 모드 실행

빌드 없이 개발 모드로 실행하는 방법:

```bash
# Electron 앱 실행 (개발 모드)
cd electron && npm run dev

# 또는 Electron만 실행 (Python은 자동 연결)
cd electron && npx electron .
```

개발 모드에서는:
- Python 백엔드: `python -m src.ipc.main`으로 실행
- Electron: 소스 코드 직접 실행

## 빌드 트러블슈팅

### PyInstaller 오류

**문제**: `ModuleNotFoundError: No module named 'xxx'`

**해결**: `build.py`에 `--hidden-import` 추가

```python
"--hidden-import", "missing_module",
```

### SSL 인증서 오류

**문제**: pip 설치 시 SSL 오류

**해결**:
```bash
pip install pyinstaller --trusted-host pypi.org --trusted-host files.pythonhosted.org
```

### Electron Builder 오류

**문제**: `Cannot find module 'xxx'`

**해결**:
```bash
cd electron && rm -rf node_modules && npm install
cd renderer && rm -rf node_modules && npm install
```

### 빌드 파일 크기

| 구성요소 | 크기 | 포함 내용 |
|----------|------|-----------|
| backend.exe | ~55MB | Python + 라이브러리 (numpy, pandas 등) |
| AutoStock Setup.exe | ~130MB | Electron + Chromium + backend.exe |

## 버전 관리

버전 변경 시 수정할 파일:

1. `electron/package.json`
   ```json
   {
     "version": "1.0.0"
   }
   ```

2. `electron/renderer/package.json`
   ```json
   {
     "version": "1.0.0"
   }
   ```

빌드 후 출력 파일명: `AutoStock Setup {version}.exe`
