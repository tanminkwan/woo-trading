# 설치 가이드

AutoStock 데스크톱 앱 설치 및 설정 방법입니다.

## 다운로드

배포된 설치 파일을 다운로드합니다:

- **Windows**: `AutoStock Setup 1.0.0.exe`

## 설치

### Windows 설치

1. `AutoStock Setup 1.0.0.exe` 실행
2. 설치 경로 선택 (기본: `C:\Users\{사용자}\AppData\Local\Programs\AutoStock`)
3. 설치 완료

### 설치 후 폴더 구조

```
C:\Users\{사용자}\AppData\Local\Programs\AutoStock\
├── AutoStock.exe                    # 메인 실행파일
├── Uninstall AutoStock.exe          # 제거 프로그램
│
└── resources/
    ├── config/
    │   ├── .env                     # API 인증 정보 (직접 생성)
    │   ├── trading_config.yaml      # 자동매매 설정
    │   └── trading_config.example.yaml
    │
    └── python-backend/
        └── backend.exe              # Python 백엔드
```

## 설정

### 1. 한국투자증권 API 발급

1. [KIS Developers](https://apiportal.koreainvestment.com/) 가입
2. 로그인 → API 신청
3. APP KEY, APP SECRET 발급받기

> **참고**: 모의투자용과 실전투자용 API Key가 다릅니다.

### 2. .env 파일 생성

설치 폴더의 `resources/config/` 경로에 `.env` 파일을 생성합니다.

**경로**:
```
C:\Users\{사용자}\AppData\Local\Programs\AutoStock\resources\config\.env
```

**.env 파일 내용**:

```env
# API 인증 정보 (한국투자증권에서 발급)
APP_KEY=PSXXXXXXXXXXXXXXXXXXXXXXXXX
APP_SECRET=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# 계좌번호 (XXXXXXXX-XX 형식)
ACCOUNT_NO=12345678-01

# 환경 설정
# prod: 실전투자
# dev: 모의투자
ENV=dev
```

> **중요**: `.env` 파일에는 민감한 정보가 포함되어 있습니다. 절대 타인과 공유하지 마세요.

### 3. 자동매매 설정 (선택)

`resources/config/trading_config.yaml` 파일을 수정하여 자동매매할 종목을 설정합니다.

```yaml
settings:
  default_interval: 60    # 모니터링 주기 (초)
  max_daily_trades: 10    # 일일 최대 거래 횟수

stocks:
  # 범위 매매 전략 예시
  - code: "005930"
    name: "삼성전자"
    strategy: "range_trading"
    max_amount: 1000000
    buy_price: 52000        # 이 가격 이하일 때 매수
    sell_price: 58000       # 이 가격 이상일 때 매도
    enabled: true
    priority: 1

  # 변동성 돌파 전략 예시
  - code: "000660"
    name: "SK하이닉스"
    strategy: "volatility_breakout"
    max_amount: 500000
    enabled: false          # 비활성화
    priority: 2
    vb_params:
      k: 0.5
      target_profit_rate: 2.0
      stop_loss_rate: -2.0
      sell_at_close: true
```

## 실행

바탕화면 또는 시작 메뉴에서 **AutoStock** 실행

### 첫 실행 시

1. 앱이 시작되면 Python 백엔드가 자동으로 연결됩니다
2. 대시보드에서 "시작" 버튼을 클릭하여 자동매매 시작
3. 설정 페이지에서 종목 추가/수정 가능

### 화면 구성

| 메뉴 | 기능 |
|------|------|
| **대시보드** | 엔진 상태, 종목 현황, 최근 거래 |
| **설정** | 종목 추가/삭제, 전략 설정 |
| **거래로그** | 매수/매도 기록 조회 |
| **백테스트** | 과거 데이터 기반 전략 시뮬레이션 |

## 문제 해결

### "Python process not running" 오류

**증상**: 앱 시작 시 "Error: Python process not running" 메시지

**원인 및 해결**:
1. 앱을 완전히 종료 후 재시작
2. 작업 관리자에서 `backend.exe` 프로세스가 있다면 종료 후 재시작

### "Authentication failed" 오류

**증상**: 시작 버튼 클릭 시 인증 실패

**원인 및 해결**:
1. `.env` 파일이 올바른 위치에 있는지 확인
2. APP_KEY, APP_SECRET 값이 정확한지 확인
3. API Key가 만료되었다면 KIS Developers에서 재발급

### 설정 파일을 찾을 수 없음

**증상**: 종목 목록이 비어있음

**해결**:
1. `resources/config/trading_config.yaml` 파일 존재 확인
2. 없다면 `trading_config.example.yaml`을 복사하여 생성

### 토큰 발급 제한 (EGW00133)

**증상**: "토큰 발급 제한" 오류

**원인**: 토큰은 1분에 1회만 발급 가능

**해결**: 60초 이상 대기 후 재시도

## 제거

### Windows 제거

방법 1: 설치 폴더의 `Uninstall AutoStock.exe` 실행

방법 2: Windows 설정 → 앱 → AutoStock → 제거

### 설정 파일 정리

제거 후에도 설정 파일은 남아있을 수 있습니다:
```
C:\Users\{사용자}\AppData\Local\Programs\AutoStock\resources\config\
```

완전 삭제를 원하면 해당 폴더를 수동으로 삭제하세요.

## 업데이트

1. 기존 앱 제거 (설정 파일은 보존됨)
2. 새 버전 설치파일 실행
3. 같은 경로에 설치하면 기존 `.env` 및 `trading_config.yaml` 유지됨

## 보안 권장사항

1. **API Key 보호**: `.env` 파일을 타인과 공유하지 마세요
2. **모의투자 먼저**: 실전투자 전 반드시 모의투자로 테스트하세요
3. **소액 테스트**: 처음에는 소액으로 시작하세요
4. **모니터링**: 자동매매 실행 중 주기적으로 상태를 확인하세요

## 시스템 요구사항

| 항목 | 최소 사양 |
|------|-----------|
| OS | Windows 10 64-bit 이상 |
| RAM | 4GB 이상 |
| 저장공간 | 500MB 이상 |
| 네트워크 | 인터넷 연결 필수 |
