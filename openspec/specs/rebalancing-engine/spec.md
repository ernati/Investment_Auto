# Spec: Rebalancing Engine

**Capability:** `rebalancing-engine`  
**Source:** `Scripts/modules/rebalancing_engine.py`  
**Last synced:** 2026-04-18

---

## Purpose

포트폴리오 스냅샷을 받아 리밸런싱 필요 여부를 판단하고, 구체적인 매매 주문 목록(`RebalancePlan`)을 생성한다. 실제 주문 실행은 하지 않는다 — 계획 생성에만 집중.

---

## Interface

### Input

```python
RebalancingEngine(config_loader: PortfolioConfigLoader)

create_rebalance_plan(
    portfolio_snapshot: PortfolioSnapshot,
    is_calendar_triggered: bool = False
) -> RebalancePlan

apply_guardrails(plan: RebalancePlan) -> tuple[RebalancePlan, str]
```

### Output: RebalancePlan

```python
@dataclass
class RebalancePlan:
    portfolio_id: str
    timestamp: datetime
    portfolio_snapshot: PortfolioSnapshot
    should_rebalance: bool        # False이면 orders는 비어 있음
    rebalance_reason: str
    orders: List[RebalanceOrder]
    total_orders: int
    total_delta_value: float      # 전체 거래 금액 합계 (절대값)
    target_weights: Dict[str, float]
    current_weights: Dict[str, float]
```

### Output: RebalanceOrder

```python
@dataclass
class RebalanceOrder:
    ticker: str
    action: Literal["buy", "sell"]
    target_value: float           # 목표 평가액 (KRW)
    current_value: float          # 현재 평가액 (KRW)
    delta_value: float            # 매수(+) 또는 매도(-) 금액
    delta_weight: float           # 비중 차이
    estimated_quantity: int       # 추정 수량 (BTC는 항상 1)
    estimated_price: float        # 추정 단가
    exchange: Optional[str]       # 해외주식만 있음 (예: "NYSE", "NASD")
```

---

## Rebalancing Mode Decision

```
Config: rebalance/mode = "BAND" | "CALENDAR" | "HYBRID"

BAND mode:
  band_breach? ──YES──▶ rebalance
               ──NO───▶ skip

CALENDAR mode:
  is_calendar_triggered? ──YES──▶ rebalance
                         ──NO───▶ skip

HYBRID mode (default):
  band_breach OR is_calendar_triggered? ──YES──▶ rebalance
                                        ──NO───▶ skip
```

**주의:** `is_calendar_triggered`는 `Scheduler`가 결정해서 넘겨줘야 한다. 현재 `portfolio_rebalancing.py`의 `run_once()`는 이 값을 항상 `False`로 넘긴다 — HYBRID 모드에서 Calendar 트리거가 실질적으로 작동하지 않는 상태.

---

## Band Breach Detection

```
Config:
  rebalance/band/type  = "ABS" | "REL"
  rebalance/band/value = float  (예: 0.05)

ABS 방식 (절대값 밴드):
  lower = target_weight - band_value
  upper = target_weight + band_value
  breach = current_weight < lower OR current_weight > upper

REL 방식 (상대값 밴드):
  lower = target_weight * (1 - band_value)
  upper = target_weight * (1 + band_value)
  breach = current_weight < lower OR current_weight > upper
```

하나라도 breach된 종목이 있으면 전체 포트폴리오를 리밸런싱한다 (부분 리밸런싱 없음).

---

## Order Generation Logic

```
usable_total = total_value * (1 - cash_buffer_ratio)

for ticker, target_weight in target_weights:
  target_value  = usable_total * target_weight
  current_value = portfolio_snapshot.positions[ticker].evaluation (or 0)
  delta_value   = target_value - current_value

  if |delta_value| < min_order_krw:
    skip  ← 최소 주문 금액 미달

  if price <= 0:
    skip  ← 가격 정보 없음 (경고 로그)

  if ticker == "bitcoin":
    estimated_quantity = 1  ← BTC는 금액 기반 주문, 수량은 항상 1
  else:
    estimated_quantity = int(|delta_value| / price)
    if estimated_quantity == 0: skip

  exchange = overseas_exchanges.get(ticker)  ← 해외주식만 있음
```

---

## Target Weight Structure (Config)

엔진이 읽는 설정 구조:

```json
{
  "target_weights": {
    "stocks": {
      "005930": 0.30,
      "069500": 0.20
    },
    "bonds": {
      "114820": 0.10
    },
    "overseas_stocks": {
      "AAPL": { "exchange": "NASD", "weight": 0.15 },
      "SPY":  { "exchange": "NYSE", "weight": 0.10 }
    },
    "coin": {
      "bitcoin": 0.15
    }
  }
}
```

`_flatten_target_weights()`가 이를 `{"005930": 0.30, "AAPL": 0.15, "bitcoin": 0.15, ...}` 형태로 변환.  
`_extract_overseas_exchanges()`가 `{"AAPL": "NASD", "SPY": "NYSE"}` 맵을 별도로 추출.

---

## Guardrails (apply_guardrails)

가드레일은 `config_advanced.json`에서만 로드. 없으면 원본 plan 그대로 통과.

```
적용 순서:

1. max_single_order_krw (단일 주문 금액 상한)
   |delta_value| > limit → scale down (수량 비례 축소)
   수량이 0이 되면 제거

2. max_orders_per_run (최대 주문 개수)
   초과 시 |delta_value| 큰 순서로 상위 N개만 유지

3. max_turnover_per_run (최대 회전율)
   total_delta / total_value > limit → 전체 주문 비례 축소

각 단계 후 min_order_krw 미달 주문 재제거
```

**설계 의도:** 가드레일은 스킵이 아니라 **점진적 조정**. 한도를 초과해도 가능한 범위 내에서 최대한 실행.

---

## Configuration Parameters

| 파라미터 | Config 경로 | 기본값 | 소스 |
|---------|------------|--------|------|
| 리밸런싱 모드 | `rebalance/mode` | `"HYBRID"` | basic |
| 밴드 타입 | `rebalance/band/type` | `"ABS"` | basic |
| 밴드 값 | `rebalance/band/value` | `0.05` | basic |
| 현금 버퍼 비율 | `trade/cash_buffer_ratio` | `0.02` | basic |
| 최소 주문 금액 | `trade/min_order_krw` | `100000` | basic |
| 단일 주문 상한 | `risk_guardrails/max_single_order_krw` | `None` | **advanced** |
| 최대 주문 개수 | `risk_guardrails/max_orders_per_run` | `None` | **advanced** |
| 최대 회전율 | `risk_guardrails/max_turnover_per_run` | `None` | **advanced** |

---

## Invariants

1. `should_rebalance = False`이면 `orders`는 반드시 빈 리스트
2. BTC 주문의 `estimated_quantity`는 항상 `1` — 실제 수량이 아님
3. 해외주식 주문만 `exchange` 필드가 있음 (국내주식은 `None`)
4. 가드레일은 원본 plan을 mutate하지 않음 — 새 `RebalancePlan` 객체 반환
5. `apply_guardrails` 후 모든 주문은 `|delta_value| >= min_order_krw` 보장

---

## Known Issues

- `run_once()`에서 `is_calendar_triggered=False`를 하드코딩 전달 → CALENDAR/HYBRID 모드에서 Calendar 조건 미작동
- BTC `estimated_quantity=1` 컨벤션이 가드레일 계산에 영향: `max_single_order_krw` 적용 시 BTC 주문은 수량 기반 축소 불가 (수량=1이므로 항상 0 또는 1)
- `check_guardrails()`는 deprecated, 내부적으로 `apply_guardrails()` 호출
