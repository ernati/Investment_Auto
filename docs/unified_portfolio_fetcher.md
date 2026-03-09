# Unified Portfolio Fetcher Module (unified_portfolio_fetcher.py)

## 개요

KIS(한국투자증권)의 주식/채권 포트폴리오와 Upbit의 비트코인 포트폴리오를 통합하여 조회하는 모듈입니다. 포트폴리오 리밸런싱 시 전체 자산을 하나의 스냅샷으로 관리할 수 있습니다.

## 주요 기능

- **KIS 주식/채권 조회**: 기존 KIS Portfolio Fetcher 활용
- **Upbit 비트코인 조회**: Upbit API 클라이언트 활용
- **통합 스냅샷 생성**: 전체 자산을 하나의 PortfolioSnapshot으로 통합
- **총 현금 계산**: KIS 현금 + Upbit KRW 현금

## 클래스

### UnifiedPortfolioFetcher

KIS와 Upbit의 포트폴리오를 통합 조회하는 클래스입니다.

```python
from modules.unified_portfolio_fetcher import UnifiedPortfolioFetcher, create_unified_fetcher
from modules.kis_auth import KISAuth

# KIS 인증 설정
kis_auth = KISAuth(
    appkey="YOUR_APP_KEY",
    appsecret="YOUR_APP_SECRET",
    account="YOUR_ACCOUNT",
    product="01",
    htsid="YOUR_HTS_ID",
    env="demo"
)

# 통합 페처 생성
fetcher = create_unified_fetcher(kis_auth, env="demo")

# 통합 포트폴리오 스냅샷 조회
snapshot = fetcher.fetch_unified_portfolio_snapshot(
    portfolio_id="portfolio-001",
    price_source="last",
    extra_tickers=["005930", "000660", "035420", "bitcoin"]
)

print(f"총 현금: {snapshot.cash:,}원")
print(f"총 자산: {snapshot.total_value:,}원")
```

## 메서드

### fetch_unified_portfolio_snapshot

KIS와 Upbit의 통합 포트폴리오 스냅샷을 생성합니다.

```python
snapshot = fetcher.fetch_unified_portfolio_snapshot(
    portfolio_id="portfolio-001",
    price_source="last",      # "last" 또는 "close"
    extra_tickers=["005930", "000660", "bitcoin"]
)
```

**매개변수:**
- `portfolio_id` (str): 포트폴리오 ID
- `price_source` (str): 가격 소스 ("last" 또는 "close")
- `extra_tickers` (List[str], optional): 추가로 조회할 티커 목록 (bitcoin 포함 가능)

**반환값:**
- `PortfolioSnapshot`: 통합 포트폴리오 스냅샷

**스냅샷 내용:**
- `cash`: KIS 현금 + Upbit KRW 현금
- `positions`: 주식 + 비트코인 포지션
- `total_value`: 전체 자산 (현금 + 포지션 평가액)

### get_upbit_cash

Upbit KRW 잔고만 조회합니다.

```python
upbit_krw = fetcher.get_upbit_cash()
print(f"Upbit KRW: {upbit_krw:,}원")
```

### get_bitcoin_info

비트코인 상세 정보를 조회합니다.

```python
btc_info = fetcher.get_bitcoin_info()
print(f"BTC 잔액: {btc_info['btc_balance']:.8f}")
print(f"BTC 평가액: {btc_info['btc_value']:,.0f}원")
print(f"현재가: {btc_info['current_price']:,.0f}원")
```

## 전역 함수

### create_unified_fetcher

통합 포트폴리오 페처를 생성하는 팩토리 함수입니다.

```python
from modules.unified_portfolio_fetcher import create_unified_fetcher

fetcher = create_unified_fetcher(
    kis_auth=kis_auth,
    env="demo"  # 또는 "real"
)
```

## 비트코인 포지션 처리

비트코인은 다른 주식/채권과 다르게 처리됩니다:

1. **티커**: `"bitcoin"` 문자열 사용
2. **수량**: 소수점 (예: 0.005 BTC)
3. **PositionSnapshot**: 
   - `quantity`: 1로 설정 (비트코인은 수량 기반이 아닌 금액 기반)
   - `price`: 현재 비트코인 가격
   - `evaluation`: 실제 평가액 (btc_balance * price)
   - `_btc_balance`: 실제 BTC 보유량 (주문 시 필요)

## 통합 현금 계산

```python
# 스냅샷의 cash는 다음과 같이 계산됨
total_cash = kis_cash + upbit_krw

# 개별 조회도 가능
upbit_krw = fetcher.get_upbit_cash()
```

## 설정 (config_basic.json)

포트폴리오에 비트코인을 포함하려면 `config_basic.json`에 coin 카테고리 추가:

```json
{
  "target_weights": {
    "stocks": {
      "005930": 0.35,
      "000660": 0.25,
      "035420": 0.25
    },
    "bonds": {
      "KR103502GA34": 0.0
    },
    "coin": {
      "bitcoin": 0.15
    }
  }
}
```

## 데모 모드 동작

- **KIS**: 기존 모의투자 환경 사용
- **Upbit**: 메모리 기반 가상 거래 (프로세스 종료 시 초기화)
- **통합 스냅샷**: 두 시스템의 데이터를 하나로 통합

## 관련 모듈

- [kis_portfolio_fetcher.py](kis_portfolio_fetcher.md): KIS 포트폴리오 조회
- [upbit_api_client.py](upbit_api_client.md): Upbit API 클라이언트
- [portfolio_models.py](portfolio_models.md): 포트폴리오 데이터 모델
- [rebalancing_engine.py](rebalancing_engine.md): 리밸런싱 계획 생성

## 사용 예시

### portfolio_rebalancing.py에서 사용

```python
# 기존 코드
# self.portfolio_fetcher = KISPortfolioFetcher(self.kis_auth)

# 변경된 코드 (통합 페처 사용)
self.portfolio_fetcher = create_unified_fetcher(self.kis_auth, kis_env)

# 통합 스냅샷 조회
portfolio_snapshot = self.portfolio_fetcher.fetch_unified_portfolio_snapshot(
    portfolio_id,
    price_source=self.config.get_basic("rebalance/price_source", "last"),
    extra_tickers=all_tickers  # bitcoin 포함
)
```

## 테스트

```bash
# 통합 포트폴리오 페처 테스트
python Scripts/tests/kis_debug.py --upbit
```
