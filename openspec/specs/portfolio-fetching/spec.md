# Spec: Portfolio Data Fetching

**Capability:** `portfolio-fetching`  
**Source:** `Scripts/modules/unified_portfolio_fetcher.py`, `kis_portfolio_fetcher.py`  
**Last synced:** 2026-04-18

---

## Purpose

KIS 계좌(국내주식·채권·해외주식)와 Upbit 계좌(BTC)를 조회해 단일 `PortfolioSnapshot`으로 병합한다. 리밸런싱 엔진과 웹 대시보드 양쪽에 데이터를 공급한다.

---

## Interface

### 생성

```python
# 권장: Factory 함수 사용
fetcher = create_unified_fetcher(
    kis_auth: KISAuth,
    env: str = "demo",
    overseas_stocks_config: Optional[Dict[str, Dict]] = None
    # overseas_stocks_config 형태: {"SPY": {"exchange": "AMEX", "weight": 0.4}, ...}
)

# 직접 생성 시
fetcher = UnifiedPortfolioFetcher(
    kis_auth: KISAuth,
    upbit_client: Optional[UpbitClient] = None,  # None이면 env 기반 자동 생성
    env: str = "demo",
    overseas_stocks_config: Optional[Dict[str, Dict]] = None
)
```

### 주요 메서드

```python
# 리밸런싱용 (전체 통합 스냅샷)
fetch_unified_portfolio_snapshot(
    portfolio_id: str,
    price_source: str = "last",   # "last" | "close"
    extra_tickers: Optional[List[str]] = None
) -> PortfolioSnapshot

# 웹 서버용 (dict 반환)
get_portfolio_snapshot() -> Dict

# 개별 조회
get_upbit_cash() -> float
get_bitcoin_info() -> Dict
```

---

## Data Flow: fetch_unified_portfolio_snapshot

```
fetch_unified_portfolio_snapshot(portfolio_id, price_source, extra_tickers)
  │
  ├─ 1. KIS 조회
  │     extra_tickers에서 "bitcoin" 제외
  │     KISPortfolioFetcher.fetch_portfolio_snapshot(...)
  │     → kis_snapshot: PortfolioSnapshot (국내주식 + 채권 + 해외주식, KIS 현금)
  │
  ├─ 2. Upbit 조회
  │     UpbitClient.get_btc_evaluation()
  │     → upbit_krw: float (Upbit KRW 잔고)
  │     → upbit_btc_value: float (BTC 평가액 KRW)
  │     → btc_balance: float (실제 BTC 수량)
  │     → btc_price: float (현재 BTC 단가)
  │
  ├─ 3. 병합
  │     total_cash = kis_snapshot.cash + upbit_krw
  │     unified_snapshot = PortfolioSnapshot(cash=total_cash)
  │     for ticker in kis_snapshot.positions: unified_snapshot.positions[ticker] = position
  │
  ├─ 4. BTC 포지션 추가 (btc_balance > 0 OR "bitcoin" in extra_tickers)
  │     PositionSnapshot(ticker="bitcoin", quantity=1, price=btc_price)
  │     .evaluation = upbit_btc_value   ← 수동 override
  │     ._btc_balance = btc_balance     ← 동적 속성 (실제 BTC 수량)
  │
  └─ 5. _recalculate() 호출 → total_value, stocks_value 갱신
```

---

## Output: PortfolioSnapshot

```python
@dataclass
class PortfolioSnapshot:
    portfolio_id: str
    timestamp: datetime
    cash: float                           # KIS KRW + Upbit KRW
    positions: Dict[str, PositionSnapshot]
    stocks_value: float                   # positions 합계 (자동 계산)
    total_value: float                    # cash + stocks_value (자동 계산)
```

```python
@dataclass
class PositionSnapshot:
    ticker: str
    quantity: int                         # BTC는 항상 1 (컨벤션)
    price: float                          # BTC는 현재 단가
    evaluation: float                     # BTC는 upbit_btc_value로 override됨

# BTC에만 추가되는 동적 속성:
position._btc_balance: float             # 실제 BTC 보유 수량
```

**중요:** `PositionSnapshot.evaluation`은 `quantity * price`로 자동 계산되지만, BTC의 경우 `quantity=1`이므로 evaluation을 수동으로 실제 BTC 평가액으로 override한다.

---

## 두 가지 조회 경로

| 용도 | 메서드 | 반환 타입 | 특징 |
|------|--------|-----------|------|
| 리밸런싱 | `fetch_unified_portfolio_snapshot()` | `PortfolioSnapshot` | 리밸런싱 엔진 입력 형식 |
| 웹 대시보드 | `get_portfolio_snapshot()` | `Dict` | KIS holdings API 별도 호출, 채권 TODO |

`get_portfolio_snapshot()`은 웹 서버용 fallback 경로. 메인 실행 경로에서는 사용되지 않음.

---

## Dependencies

```
UnifiedPortfolioFetcher
  ├── KISPortfolioFetcher   ← 국내/해외 주식·채권 조회
  │     └── kis_api_client  ← KIS REST API 호출
  └── UpbitClient           ← BTC 잔고·가격 조회
```

`price_source` 파라미터는 `KISPortfolioFetcher`로 전달되어 현재가(`"last"`) 또는 전일종가(`"close"`) 선택.

---

## Configuration Parameters

| 파라미터 | Config 경로 | 기본값 |
|---------|------------|--------|
| 가격 소스 | `rebalance/price_source` | `"last"` |
| 해외주식 설정 | `target_weights/overseas_stocks` | `{}` |

---

## Invariants

1. **"bitcoin" 티커는 KIS에 전달하지 않는다** — `extra_tickers`에서 명시적으로 제외
2. **BTC `quantity`는 항상 1** — 실제 BTC 수량은 `._btc_balance`에 저장
3. **BTC `evaluation`은 항상 수동 override** — `quantity * price`를 신뢰하지 말 것
4. **Upbit 조회 실패 시 BTC 포지션 없음** — 경고 로그만, 예외 없음
5. **`_recalculate()` 필수** — positions 수동 조작 후 반드시 호출해야 `total_value` 정확

---

## Known Issues

- `get_portfolio_snapshot()` (웹용)의 채권 분류가 미구현 (`bonds: []` 하드코딩)
- Upbit 실패 시 BTC 가격 재조회(`get_bitcoin_price()`)하지만 이미 조회 실패 상태면 의미 없음
- `_btc_balance`는 dataclass 외부 동적 속성 — 타입 힌트 없음, 접근 전 `hasattr` 확인 필요
