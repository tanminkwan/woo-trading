# 한국투자증권 OpenAPI 주식 자동매매 프로그램

한국투자증권 OpenAPI를 활용한 Python 주식 자동매매 프로그램입니다.

## 기능

- **시세 조회**: 현재가, 호가, 일별 시세
- **계좌 조회**: 잔고, 보유종목, 주문가능금액
- **주문**: 매수/매도 (시장가/지정가)
- **주문 내역**: 당일 주문/체결 조회
- **자동매매 엔진**: YAML 설정 기반 자동 매매
- **웹 관리 화면**: 종목 등록/관리, 엔진 제어, 거래 로그

## 설치

```bash
# 저장소 클론
git clone https://github.com/your-repo/auto-stock.git
cd auto-stock

# 의존성 설치
pip install -r requirements.txt
```

## 설정

### 1. 한국투자증권 API 발급

1. [KIS Developers](https://apiportal.koreainvestment.com/) 가입
2. API 신청 → APP KEY, APP SECRET 발급

### 2. 환경변수 설정

`.env` 파일 생성:

```env
# API 인증 정보
APP_KEY=your_app_key
APP_SECRET=your_app_secret

# 계좌번호 (XXXXXXXX-XX 형식)
ACCOUNT_NO=12345678-01

# 환경 설정 (prod: 실전투자, dev: 모의투자)
ENV=dev
```

## 사용법

### CLI 명령어

```bash
# 현재가 조회
python main.py price 005930

# 호가 조회
python main.py asking 005930

# 일별 시세 (최근 10일)
python main.py daily 005930 -n 10

# 계좌 잔고 조회
python main.py balance

# 주문가능금액 조회
python main.py deposit

# 매수 주문 (지정가: 70,000원에 10주)
python main.py buy 005930 10 70000

# 매수 주문 (시장가: 가격을 0으로)
python main.py buy 005930 10 0

# 매도 주문
python main.py sell 005930 5 71000

# 당일 주문 내역 조회
python main.py orders

# 특정일 주문 내역 조회
python main.py orders -d 20251216
```

### Python 코드에서 사용

```python
from src.factory import KISClient

# 클라이언트 초기화 (.env에서 설정 로드)
client = KISClient()
client.authenticate()

# 시세 조회
price = client.stock.get_price("005930")
print(f"삼성전자 현재가: {price.current_price:,}원")

# 호가 조회
asking = client.stock.get_asking_price("005930")
print(f"매수호가1: {asking.buy_prices[0]:,}원")

# 잔고 조회
balance = client.account.get_balance()
for h in balance.holdings:
    print(f"{h.stock_name}: {h.quantity}주, 수익률 {h.profit_rate}%")

# 매수 주문 (지정가)
result = client.order.buy("005930", quantity=1, price=70000)
if result.success:
    print(f"주문번호: {result.order_no}")

# 매도 주문 (시장가)
result = client.order.sell("005930", quantity=1, price=0)
```

### 직접 설정 주입

```python
from src.factory import KISClient
from src.infrastructure.config import Config

# 환경변수 대신 직접 설정
config = Config.create(
    app_key="your_app_key",
    app_secret="your_app_secret",
    account_no="12345678-01",
    is_production=False,  # True: 실전, False: 모의
)

client = KISClient(config)
```

## 프로젝트 구조

```
auto-stock/
├── .env                          # 환경변수
├── main.py                       # CLI 인터페이스
├── requirements.txt
│
├── src/
│   ├── factory.py                # 의존성 주입 팩토리
│   │
│   ├── domain/                   # 도메인 계층
│   │   ├── models.py             # 데이터 모델
│   │   └── interfaces.py         # 인터페이스 정의
│   │
│   ├── infrastructure/           # 인프라 계층
│   │   ├── config.py             # 설정 관리
│   │   ├── http_client.py        # HTTP 클라이언트
│   │   └── auth.py               # 인증 처리
│   │
│   └── application/              # 애플리케이션 계층
│       ├── stock_service.py      # 시세 서비스
│       ├── account_service.py    # 계좌 서비스
│       └── order_service.py      # 주문 서비스
│
└── tests/                        # 테스트
    ├── conftest.py               # 테스트 픽스처
    ├── test_models.py
    ├── test_config.py
    ├── test_stock_service.py
    ├── test_account_service.py
    └── test_order_service.py
```

## 아키텍처

### SOLID 원칙 적용

| 원칙 | 적용 |
|------|------|
| **SRP** | 클래스별 단일 책임 (Config, Auth, HttpClient 분리) |
| **OCP** | 인터페이스 기반 설계로 확장에 열림 |
| **LSP** | 구현체 교체 가능 (Mock 테스트) |
| **ISP** | 서비스 인터페이스 분리 (Stock, Account, Order) |
| **DIP** | 추상화 의존, Factory 패턴 적용 |

### 계층 구조

```
┌─────────────────────────────────────┐
│           main.py (CLI)             │
└─────────────────────────────────────┘
                  │
┌─────────────────────────────────────┐
│        factory.py (DI Container)    │
└─────────────────────────────────────┘
                  │
┌─────────────────────────────────────┐
│    application/ (서비스 계층)        │
│  - StockService                     │
│  - AccountService                   │
│  - OrderService                     │
└─────────────────────────────────────┘
                  │
┌─────────────────────────────────────┐
│    domain/ (도메인 계층)             │
│  - Models (DTO)                     │
│  - Interfaces (추상화)              │
└─────────────────────────────────────┘
                  │
┌─────────────────────────────────────┐
│    infrastructure/ (인프라 계층)     │
│  - Config, Auth, HttpClient         │
└─────────────────────────────────────┘
```

## 테스트

```bash
# 전체 테스트 실행
python -m pytest tests/ -v

# 특정 테스트 파일 실행
python -m pytest tests/test_stock_service.py -v

# 커버리지 포함
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

### 테스트 커버리지

| 모듈 | 커버리지 |
|------|----------|
| domain/models.py | 90% |
| application/ | 85-92% |
| engine/config_parser.py | 91% |
| **전체** | **62%** |

총 87개 테스트 케이스

## 주의사항

- **API 호출 제한**: 초당 20회 제한 준수
- **토큰 발급 제한**: 1분에 1회
- **장 운영시간**: 09:00~15:30 (주문 가능)
- **실전/모의 구분**: `.env`의 `ENV` 값으로 전환
- **API 키 보안**: `.env` 파일은 절대 커밋하지 마세요

## 주요 종목코드

| 종목명 | 코드 |
|--------|------|
| 삼성전자 | 005930 |
| SK하이닉스 | 000660 |
| LG에너지솔루션 | 373220 |
| 삼성바이오로직스 | 207940 |
| 현대차 | 005380 |
| 기아 | 000270 |
| NAVER | 035420 |
| 카카오 | 035720 |
| KODEX 200 | 069500 |
| KODEX 코스닥150 | 229200 |

## 자동매매 엔진

### 웹 서버 실행

```bash
python run_web.py
```

브라우저에서 http://localhost:8000 접속

### 웹 화면 기능

| 페이지 | 기능 |
|--------|------|
| **대시보드** | 엔진 상태, 종목 현황, 실시간 모니터링 |
| **설정** | 종목 추가/삭제, 활성화 토글 |
| **거래로그** | 매수/매도 기록 조회 |

### YAML 설정 파일

`config/trading_config.yaml`:

```yaml
settings:
  default_interval: 60    # 기본 모니터링 주기 (초)
  max_daily_trades: 10    # 일일 최대 거래 횟수

stocks:
  # 범위 매매 전략
  - code: "005930"
    name: "삼성전자"
    strategy: "range_trading"   # 전략 선택
    max_amount: 1000000
    buy_price: 52000            # 매수 희망가 (이하일 때 매수)
    sell_price: 58000           # 매도 희망가 (이상일 때 매도)
    enabled: true
    priority: 1

  # 변동성 돌파 전략
  - code: "000660"
    name: "SK하이닉스"
    strategy: "volatility_breakout"
    max_amount: 500000
    enabled: true
    priority: 2
    vb_params:
      k: 0.5                    # 변동성 계수
      target_profit_rate: 2.0   # 목표 수익률 (%)
      stop_loss_rate: -2.0      # 손절 수익률 (%)
      sell_at_close: true       # 장 마감 전 매도
```

## 거래 전략

### 1. 범위 매매 (Range Trading)

설정한 가격 범위에서 매수/매도하는 전략

| 파라미터 | 설명 |
|----------|------|
| `buy_price` | 매수 희망가 (이하일 때 매수) |
| `sell_price` | 매도 희망가 (이상일 때 매도) |

**매매 로직:**
- 현재가 ≤ buy_price → 매수
- 현재가 ≥ sell_price → 매도

### 2. 변동성 돌파 (Volatility Breakout)

래리 윌리엄스의 변동성 돌파 전략

**목표가 계산:**
```
목표가 = 당일시가 + (전일고가 - 전일저가) × K
```

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `k` | 0.5 | 변동성 계수 (0.1~1.0) |
| `target_profit_rate` | 2.0 | 목표 수익률 (%) 도달 시 매도 |
| `stop_loss_rate` | -2.0 | 손절 수익률 (%) 도달 시 매도 |
| `sell_at_close` | true | 장 마감 전(15:15) 자동 매도 |

**매매 로직:**
- 현재가 ≥ 목표가 → 매수 (당일 1회)
- 수익률 ≥ target_profit_rate → 매도
- 수익률 ≤ stop_loss_rate → 손절 매도
- 15:15 이후 → 자동 매도 (sell_at_close=true)

**K값 가이드:**
| K값 | 특성 |
|-----|------|
| 0.3~0.4 | 공격적 (진입 기회 多, 손절 多) |
| 0.5 | 표준 |
| 0.6~0.7 | 보수적 (진입 기회 少, 승률 高) |

### 우선순위 (Priority)

종목별 `priority` 값으로 주문 처리 순서를 지정합니다.

| priority | 설명 |
|----------|------|
| 1 | 가장 먼저 처리 |
| 2, 3, ... | 순차적으로 처리 |
| 100 (기본값) | 우선순위 미지정 시 |

**왜 우선순위가 필요한가?**
- 주문가능금액이 한정적일 때, 여러 종목이 동시에 매수 조건을 충족하면 모든 주문이 체결되지 않음
- 우선순위가 높은 종목부터 주문하여 중요한 종목의 체결 확률을 높임

```yaml
stocks:
  - code: "005930"
    name: "삼성전자"
    priority: 1           # 1순위: 가장 먼저 주문
    ...
  - code: "000660"
    name: "SK하이닉스"
    priority: 2           # 2순위
    ...
  - code: "035420"
    name: "NAVER"
    priority: 3           # 3순위
    ...
```

### 자동매매 로직

**공통:**
1. **모니터링**: 설정된 주기마다 현재가 조회
2. **우선순위**: priority 순으로 종목 처리
3. **거래 제한**: 일일 최대 거래 횟수 초과 시 중단

**전략별 로직은 위의 [거래 전략](#거래-전략) 섹션 참조**

### API 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/api/engine/start` | POST | 엔진 시작 |
| `/api/engine/stop` | POST | 엔진 정지 |
| `/api/engine/pause` | POST | 일시정지 |
| `/api/engine/resume` | POST | 재개 |
| `/api/engine/status` | GET | 상태 조회 |
| `/api/stocks` | GET | 종목 목록 |
| `/api/stocks` | POST | 종목 추가 |
| `/api/stocks/{code}/toggle` | POST | 활성화 토글 |
| `/api/stocks/{code}/delete` | POST | 종목 삭제 |
| `/api/logs` | GET | 거래 로그 |

## 트러블슈팅

### Authentication failed 에러

웹 UI에서 `시작` 버튼 클릭 시 `Authentication failed` 에러가 발생하는 경우:

```
2025-12-16 14:55:24,457 [ERROR] Authentication failed
```

**원인**: API Key가 해지되었거나 만료된 경우

**해결 방법**:
1. [KIS Developers](https://apiportal.koreainvestment.com/)에 로그인
2. 새 API Key 발급 (APP KEY, APP SECRET)
3. `.env` 파일 업데이트:
   ```env
   APP_KEY=new_app_key
   APP_SECRET=new_app_secret
   ```
4. 웹 서버 재시작 후 다시 시도

### 토큰 발급 제한 에러

```
EGW00133: 토큰 발급 제한
```

**원인**: 토큰은 1분에 1회만 발급 가능

**해결 방법**: 60초 이상 대기 후 재시도

### API 호출 제한

**원인**: 초당 20회 API 호출 제한 초과

**해결 방법**: 모니터링 주기(`interval`)를 늘려서 API 호출 빈도 감소

## 라이선스

MIT License
