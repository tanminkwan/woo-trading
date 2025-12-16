# 한국투자증권 OpenAPI 주식 자동매매 프로그램

한국투자증권 OpenAPI를 활용한 Python 주식 자동매매 프로그램입니다.

## 기능

- **시세 조회**: 현재가, 호가, 일별 시세
- **계좌 조회**: 잔고, 보유종목, 주문가능금액
- **주문**: 매수/매도 (시장가/지정가)
- **주문 내역**: 당일 주문/체결 조회

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
python -m pytest tests/ -v --cov=src
```

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

## 라이선스

MIT License
