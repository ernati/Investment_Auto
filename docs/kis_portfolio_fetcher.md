# KIS Portfolio Fetcher Module (kis_portfolio_fetcher.py)

## 개요
한국투자증권(KIS) Open API를 통해 포트폴리오 데이터를 실시간으로 조회하는 모듈입니다.
- 계좌 현금 조회
- 보유종목 및 수량 조회
- 종목별 현재가 조회
- 포트폴리오 스냅샷 생성

## 리팩토링 이력

**v1.1 (Refactoring Release)**:
- `kis_api_utils.py` 모듈의 공유 유틸리티 함수 사용으로 리팩토링
- 중복 코드 제거: `_get_headers()` 메서드 제거
- API 응답 검증 로직을 `kis_api_utils.validate_api_response()`로 통합
- API 요청 실행을 `kis_api_utils.execute_api_request()`로 통합
- 에러 처리 로직 표준화로 코드 유지보수성 향상
- ~50% 코드 라인 수 감소 (180행 → 90행)

## 주요 기능

### 1. 계좌 잔고 조회
KIS API `/uapi/domestic-stock/v1/trading/inquire-balance` 사용

```python
balance_info = fetcher.fetch_account_balance()
# Returns:
# {
#     'cash': 1000000.0,           # 현금잔고
#     'd2_cash': 1000000.0,        # D2 현금
#     'orderable_cash': 999000.0   # 주문가능현금
# }
```

### 2. 보유종목 조회
```python
holdings = fetcher.fetch_holdings()
# Returns:
# {
#     '005930': 100,  # 삼성전자 100주
#     '000660': 50,   # SK하이닉스 50주
# }
```

### 3. 종목별 가격 조회
KIS API `/uapi/domestic-stock/v1/quotations/inquire-price` 사용

```python
price = fetcher.fetch_current_price("005930")
# Returns: 70000.0

prices = fetcher.fetch_multiple_prices(["005930", "000660"])
# Returns:
# {
#     '005930': 70000.0,
#     '000660': 60000.0
# }
```

### 4. 포트폴리오 스냅샷 생성 (통합)
현금, 보유종목, 가격을 모두 조회하여 PortfolioSnapshot 생성

```python
snapshot = fetcher.fetch_portfolio_snapshot(
    portfolio_id="portfolio-001",
    price_source="last"  # "last" 또는 "close"
)
# Returns: PortfolioSnapshot 객체
# - cash: 현금잔고
# - positions: 보유종목들
# - total_value, stocks_value: 계산된 값
```

## 클래스 설명

### KISPortfolioFetcher

#### 생성자
```python
KISPortfolioFetcher(kis_auth: KISAuth)
```

**파라미터:**
- `kis_auth`: KISAuth 인스턴스 (인증 정보 포함)

#### 속성
| 속성 | 설명 |
|------|------|
| `kis_auth` | KISAuth 인스턴스 |
| `base_url` | KIS API 기본 URL |
| `token` | 현재 액세스 토큰 (캐시) |

#### 메서드

##### fetch_account_balance()
계좌 잔고를 조회합니다.

**Returns:**
```python
{
    'cash': float,              # 현금잔고
    'd2_cash': float,           # D2 현금
    'orderable_cash': float     # 주문가능현금
}
```

**Raises:**
- `RuntimeError`: API 호출 실패
- `requests.exceptions.RequestException`: 네트워크 오류

**예시:**
```python
try:
    balance = fetcher.fetch_account_balance()
    print(f"주문가능현금: {balance['orderable_cash']:.0f} 원")
except RuntimeError as e:
    print(f"잔고 조회 실패: {e}")
```

---

##### fetch_holdings()
보유종목과 수량을 조회합니다.

**Returns:**
```python
{
    'ticker1': quantity1,
    'ticker2': quantity2,
    ...
}
```

**예시:**
```python
holdings = fetcher.fetch_holdings()
for ticker, qty in holdings.items():
    print(f"{ticker}: {qty}주")
```

---

##### fetch_current_price(ticker)
단일 종목의 현재가를 조회합니다.

**Parameters:**
- `ticker` (str): 종목코드 (예: "005930")

**Returns:**
- `float`: 현재가

**Raises:**
- `RuntimeError`: API 호출 실패
- `requests.exceptions.RequestException`: 네트워크 오류

**예시:**
```python
price = fetcher.fetch_current_price("005930")
print(f"삼성전자: {price:.0f} 원")
```

---

##### fetch_multiple_prices(tickers)
여러 종목의 현재가를 조회합니다 (비동기 아님, 순차 조회).

**Parameters:**
- `tickers` (List[str]): 종목코드 리스트

**Returns:**
```python
{
    'ticker1': price1,
    'ticker2': price2,
    ...
}
```

**주의:**
- 한 종목의 조회 실패가 전체를 중단하지 않음 (로깅만 함)
- 개별 호출보다 느릴 수 있음 (API 호출 횟수)

**예시:**
```python
tickers = ["005930", "000660", "035420"]
prices = fetcher.fetch_multiple_prices(tickers)
for ticker, price in prices.items():
    print(f"{ticker}: {price:.0f} 원")
```

---

##### fetch_portfolio_snapshot(portfolio_id, price_source, extra_tickers)
포트폴리오의 현재 상태를 스냅샷으로 생성합니다 (모든 정보 통합).

**Parameters:**
- `portfolio_id` (str): 포트폴리오 ID
- `price_source` (str): 가격 출처 ("last" 또는 "close")
- `extra_tickers` (List[str], optional): 보유하지 않은 종목이라도 가격을 조회할 티커 목록

**Returns:**
- `PortfolioSnapshot`: 포트폴리오 스냅샷 객체
  - 현금, 보유종목, 평가액, 비중 등 포함

**Process:**
1. 계좌 잔고 조회 (현금)
2. 보유종목 조회 (ticker, 수량)
3. 보유 종목과 추가 티커의 현재가 조회
4. PortfolioSnapshot 생성 (보유하지 않은 종목은 수량 0으로 추가)

**예시:**
```python
snapshot = fetcher.fetch_portfolio_snapshot(
    portfolio_id="portfolio-001",
    price_source="last",
    extra_tickers=["005930", "000660", "035420"]
)

print(f"현금: {snapshot.cash:,.0f} 원")
print(f"주식평가액: {snapshot.stocks_value:,.0f} 원")
print(f"총평가액: {snapshot.total_value:,.0f} 원")

for ticker, position in snapshot.positions.items():
    weight = snapshot.get_current_weight(ticker)
    print(f"{ticker}: {position.quantity}주, 평가액 {position.evaluation:,.0f}원 ({weight:.1%})")
```

## API 엔드포인트

### 사용하는 KIS API

| 기능 | 엔드포인트 | TR ID |
|------|-----------|-------|
| 잔고조회 | `/uapi/domestic-stock/v1/trading/inquire-balance` | TTTC8434R |
| 가격조회 | `/uapi/domestic-stock/v1/quotations/inquire-price` | FHKST01010100 |

## 에러 처리

### 일반적인 에러와 대응

```python
try:
    snapshot = fetcher.fetch_portfolio_snapshot("portfolio-001")
except RuntimeError as e:
    # API 호출 실패 (예: 계좌정보 오류, 토큰 만료)
    logger.error(f"포트폴리오 조회 실패: {e}")
except requests.exceptions.RequestException as e:
    # 네트워크 오류
    logger.error(f"네트워크 오류: {e}")
except Exception as e:
    # 예상치 못한 오류
    logger.error(f"예상치 못한 오류: {e}")
```

### 부분 실패 처리

`fetch_multiple_prices()`는 일부 종목 조회 실패 시에도 가능한 종목들의 가격을 반환합니다:

```python
prices = fetcher.fetch_multiple_prices(["005930", "999999", "000660"])
# ticker 999999가 없어도 005930과 000660은 반환됨
# 로그에 경고 메시지 기록됨
```

## 사용 패턴

### 패턴 1: 단순 가격 조회
```python
from modules.kis_auth import KISAuth
from modules.kis_portfolio_fetcher import KISPortfolioFetcher

kis_auth = KISAuth("appkey", "appsecret", "account", product="01")
fetcher = KISPortfolioFetcher(kis_auth)

# 특정 종목 가격만 필요
price = fetcher.fetch_current_price("005930")
```

### 패턴 2: 포트폴리오 전체 조회 (권장)
```python
# 한 번에 전체 정보 조회
snapshot = fetcher.fetch_portfolio_snapshot("portfolio-001")

# 이후 필요한 계산 모두 가능
current_weights = snapshot.get_current_weights()
total_value = snapshot.total_value
```

### 패턴 3: 리밸런싱 엔진과 통합
```python
from modules.rebalancing_engine import RebalancingEngine

fetcher = KISPortfolioFetcher(kis_auth)
engine = RebalancingEngine(config)

# 포트폴리오 조회
snapshot = fetcher.fetch_portfolio_snapshot("portfolio-001")

# 리밸런싱 계획 생성
plan = engine.create_rebalance_plan(snapshot)

# 주문 실행
...
```

## 성능 고려사항

### 조회 속도
- `fetch_account_balance()`: ~0.5 초
- `fetch_holdings()`: ~0.5 초 (잔고조회 API에 포함)
- `fetch_current_price()`: ~0.5 초/종목
- `fetch_portfolio_snapshot()`: ~1.5 초 + (종목 수 × 0.5초)

### 최적화 팁
1. **캐싱**: 같은 시간 내에 가격을 여러 번 조회하지 말 것
2. **배치 조회**: 여러 종목을 한 번에 조회하기
3. **API 호출 제한**: KIS API의 호출 빈도 제한 준수

## 토큰 관리

토큰은 자동으로 관리됩니다:
- 첫 호출 시: 토큰 발급 또는 저장된 토큰 재사용
- 만료 시: 자동으로 새 토큰 발급
- 캐싱: `self.token`에 유지되어 중복 발급 방지

## 로깅

기본 로거: `modules.kis_portfolio_fetcher`

```python
import logging

logger = logging.getLogger("modules.kis_portfolio_fetcher")
logger.setLevel(logging.DEBUG)

# 상세 로그 활성화 시 모든 API 호출 추적 가능
```

## 주의사항

1. **API 호출 제한**: 한국투자증권 API 호출 제한 준수 필수
2. **토큰 만료**: 6시간마다 새 토큰 발급 권장
3. **계좌 번호**: 반드시 8자리 번호 사용
4. **거래 시간**: "주문가능현금" 조회 시에만 주문 가능하게 설계
5. **시간차**: API 호출 시 약간의 시간 지연 발생 (API 자체의 특성)
