# Spec: Order Execution

**Capability:** `order-execution`  
**Source:** `Scripts/modules/order_executor.py`  
**Last synced:** 2026-04-18

---

## Purpose

`RebalancePlan`을 받아 실제 브로커 API를 호출해 주문을 실행한다. 국내주식(KIS), 해외주식(KIS Overseas), 비트코인(Upbit) 세 경로를 하나의 인터페이스로 통일한다.

---

## Interface

### Input

```python
OrderExecutor(
    config_loader: PortfolioConfigLoader,
    kis_auth: KISAuth,
    upbit_client: Optional[UpbitClient] = None,
    env: str = "demo"
)

execute_plan(plan: RebalancePlan) -> ExecutionResult
```

### Output: ExecutionResult

```python
@dataclass
class ExecutionResult:
    portfolio_id: str
    timestamp: datetime
    plan: RebalancePlan
    succeeded: bool
    error_message: Optional[str]
    executed_orders: List[Dict]        # 아래 구조 참조
    post_portfolio_snapshot: Optional[PortfolioSnapshot]
```

`executed_orders` 각 항목 구조:

```python
# 국내주식
{
    "symbol": str,
    "side": "buy" | "sell",
    "quantity": int,
    "price": float,
    "order_id": str,
    "success": bool,
}

# 해외주식 (market closed 스킵)
{
    "symbol": str,
    "side": "buy" | "sell",
    "quantity": int,
    "skipped": True,
    "market_closed": True,
    "message": str,
}

# 비트코인 매수
{
    "symbol": "bitcoin",
    "side": "buy",
    "quantity": float,         # 실제 BTC 수량
    "price": float,            # 체결 단가
    "krw_amount": float,       # 주문 금액
    "order_id": str,
    "is_demo": bool,
}

# 비트코인 매도
{
    "symbol": "bitcoin",
    "side": "sell",
    "quantity": float,
    "price": float,
    "krw_received": float,
    "pnl": float,
    "order_id": str,
    "is_demo": bool,
}
```

---

## Execution Flow

```
execute_plan(plan)
  │
  ├─ plan.should_rebalance = False → return (succeeded=True, "No rebalancing needed")
  │
  ├─ SELL orders (순서 고정)
  │     for order in sell_orders:
  │       _execute_order(order, result)
  │
  └─ BUY orders
        for order in buy_orders:
          _execute_order(order, result)


_execute_order(order)
  │
  ├─ ticker == "bitcoin" → _execute_bitcoin_order()
  │
  └─ 주식/채권
        ├─ estimated_quantity <= 0 → skip (warning)
        └─ _execute_order_live()
              │
              ├─ order.exchange != None → _execute_overseas_order()
              └─ order.exchange == None → _execute_domestic_order()
```

**불변 조건:** sell 먼저, buy 나중. 순서 변경 불가.

---

## Broker Routing

### 국내주식 (`_execute_domestic_order`)

```
order_type = config: order_policy/order_type (default: "market")

"market" → KISTrading.buy_market_order / sell_market_order
"limit"  → KISTrading.buy_limit_order / sell_limit_order
             price = int(order.estimated_price)
```

### 해외주식 (`_execute_overseas_order`)

```
1. get_overseas_market_status(order.exchange)
   └─ is_open = False → return {skipped: True, market_closed: True}
                         ← 오류 아님, executed_orders에 기록 후 계속

2. KISOverseasTrading.order(
     stock_code=order.ticker,
     exchange_code=order.exchange,    ← "NYSE", "NASD", "AMEX" 등
     order_type="buy" | "sell",
     quantity=order.estimated_quantity,
     price=str(order.estimated_price),
     order_division="00"              ← 항상 지정가
   )
```

**제약:** 해외주식은 항상 지정가(`order_division="00"`). 시장가 불가.  
`order_policy/order_type` 설정이 해외주식에는 적용되지 않음.

### 비트코인 (`_execute_bitcoin_order`)

```
매수:
  krw_amount = abs(order.delta_value)
  UpbitClient.buy_bitcoin(krw_amount)   ← KRW 금액 기반

매도:
  btc_quantity = abs(order.delta_value) / order.estimated_price
  UpbitClient.sell_bitcoin(btc_quantity) ← BTC 수량 기반
```

---

## Error Handling

| 상황 | 동작 |
|------|------|
| 해외 시장 마감 | `skipped=True`로 기록, 다음 주문 계속 |
| `estimated_quantity <= 0` | warning 로그, 스킵 |
| KIS API 오류 | `RuntimeError` 발생 → `execute_plan`이 catch → `result.succeeded=False` |
| BTC 주문 실패 | `RuntimeError` 발생 → 동일하게 전파 |
| 일반 예외 | `execute_plan`에서 catch → `result.succeeded=False`, `error_message` 설정 |

**주의:** 개별 주문 실패가 `RuntimeError`를 발생시키면 이후 주문들은 실행되지 않는다. sell 중간 실패 시 buy 주문 전체 미실행 가능.

---

## Configuration Parameters

| 파라미터 | Config 경로 | 기본값 | 소스 |
|---------|------------|--------|------|
| 주문 타입 | `order_policy/order_type` | `"market"` | advanced |
| 환경 | 생성자 `env` 인자 | `"demo"` | — |

---

## Dependencies

```
OrderExecutor
  ├── KISTrading          ← 국내주식 매매 (Scripts/modules/kis_trading.py)
  ├── KISOverseasTrading  ← 해외주식 매매 (Scripts/modules/kis_overseas_trading.py)
  ├── UpbitClient         ← BTC 매매 (Scripts/modules/upbit_api_client.py)
  └── market_hours        ← 해외 거래소 장 시간 판단
```

---

## Invariants

1. **매도 선행:** `sell_orders` 완전 실행 후 `buy_orders` 시작
2. **해외 마감 스킵은 오류 아님:** `skipped=True` 주문은 `executed_orders`에 포함되지만 성공으로 처리
3. **BTC는 금액 기반 매수, 수량 기반 매도** — 두 방향이 다른 단위를 사용
4. **해외주식은 지정가 전용** — `order_division="00"` 하드코딩
5. **env는 Upbit `is_demo` 플래그에만 영향** — KIS는 `KISAuth`의 base_url로 환경 구분

---

## Known Issues

- 개별 주문 실패 시 이후 주문이 중단됨 — partial execution 상태가 DB에 기록될 수 있음
- 해외주식 미체결 주문 추적 없음 — 지정가 주문이 체결되지 않아도 "성공"으로 기록됨
- `post_portfolio_snapshot`은 현재 채워지지 않음 (`None`) — DB 로그에서 after_weights 계산 시 current_weights를 fallback으로 사용
