# Portfolio Models Module (portfolio_models.py)

## 개요
포트폴리오 리밸런싱 시스템에서 사용하는 데이터 모델들을 정의합니다.
포트폴리오 상태, 주문, 리밸런싱 계획 등을 dataclass로 구현하여 타입 안정성과 명확성을 제공합니다.

## 주요 클래스

### 1. PriceSnapshot
종목 가격 스냅샷

```python
@dataclass
class PriceSnapshot:
    ticker: str          # 종목코드 (예: "005930")
    price: float         # 종목가격 (원)
    source: str = "last" # 가격 출처: "close" 또는 "last"
    timestamp: datetime  # 스냅샷 생성 시각
```

**사용 예:**
```python
price = PriceSnapshot(
    ticker="005930",
    price=70000.0,
    source="last",
    timestamp=datetime.now()
)
```

### 2. PositionSnapshot
보유 포지션 스냅샷

```python
@dataclass
class PositionSnapshot:
    ticker: str          # 종목코드
    quantity: int        # 보유수량
    price: float         # 현재가
    evaluation: float    # 평가금액 (수량 × 가격, 자동 계산)
```

**특징:**
- `__post_init__`: 평가금액 자동 계산
- 평가금액 = 보유수량 × 현재가

**사용 예:**
```python
position = PositionSnapshot(
    ticker="005930",
    quantity=100,
    price=70000.0
)
print(position.evaluation)  # 7000000.0
```

### 3. PortfolioSnapshot
포트폴리오 전체 스냅샷 (가장 중요)

```python
@dataclass
class PortfolioSnapshot:
    portfolio_id: str                      # 포트폴리오 ID
    timestamp: datetime = field(...)       # 스냅샷 생성 시각
    
    # 현금 정보
    cash: float = 0.0                      # 현금잔고
    
    # 포지션 정보
    positions: Dict[str, PositionSnapshot] # ticker -> PositionSnapshot
    
    # 계산된 값 (읽기 전용)
    total_value: float     # 현금 + 주식평가액
    stocks_value: float    # 주식평가액 합계
```

**메서드:**

| 메서드 | 설명 |
|--------|------|
| `add_position(ticker, qty, price)` | 포지션 추가/업데이트 |
| `update_position(ticker, qty, price)` | 포지션 업데이트 |
| `update_cash(amount)` | 현금 업데이트 |
| `get_current_weight(ticker)` | 종목의 현재 비중 조회 |
| `get_current_weights()` | 모든 종목의 현재 비중 조회 |
| `_recalculate()` | 값 재계산 (내부용) |

**사용 예:**
```python
snapshot = PortfolioSnapshot(
    portfolio_id="portfolio-001",
    timestamp=datetime.now(),
    cash=1000000.0
)

# 포지션 추가
snapshot.add_position("005930", 100, 70000.0)  # 삼성전자 100주
snapshot.add_position("000660", 50, 60000.0)   # SK하이닉스 50주

# 조회
print(snapshot.total_value)  # 8000000.0 (현금 + 주식)
print(snapshot.stocks_value) # 7000000.0 (주식만)
print(snapshot.get_current_weight("005930"))   # 0.875 (87.5%)
print(snapshot.get_current_weights())          # {'005930': 0.875, '000660': 0.375}

# 현금 업데이트
snapshot.update_cash(2000000.0)
print(snapshot.cash)  # 2000000.0
```

### 4. RebalanceOrder
리밸런싱 주문 (단일 종목)

```python
@dataclass
class RebalanceOrder:
    ticker: str          # 종목코드
    action: str          # 주문 방향: "buy" 또는 "sell"
    target_value: float  # 목표 금액
    current_value: float # 현재 금액
    delta_value: float   # 필요한 변화량 (target - current)
    delta_weight: float  # 필요한 비중 변화
    
    estimated_quantity: int = 0    # 예상 수량
    estimated_price: float = 0.0   # 예상 가격
    
    # 해외주식 정보 (v1.4 추가)
    exchange: Optional[str] = None  # 해외거래소코드 (NASD, NYSE, AMEX 등)
                                    # None이면 국내주식
```

**의미:**
- `delta_value > 0`: 매수 필요 (buy)
- `delta_value < 0`: 매도 필요 (sell)
- `exchange`: 해외주식인 경우 거래소 코드 (예: "NYSE", "NASD")

**사용 예:**
```python
# 국내주식 주문
order = RebalanceOrder(
    ticker="005930",
    action="buy",
    target_value=5000000.0,  # 목표: 500만원
    current_value=3500000.0, # 현재: 350만원
    delta_value=1500000.0,   # 150만원 더 필요
    delta_weight=0.10        # 10% 비중 추가 필요
)

# 해외주식 주문 (SPY - NYSE)
overseas_order = RebalanceOrder(
    ticker="SPY",
    action="buy",
    target_value=800000.0,
    current_value=500000.0,
    delta_value=300000.0,
    delta_weight=0.05,
    exchange="NYSE"  # 해외주식 거래소 코드
)
```

### 5. RebalancePlan
리밸런싱 계획 (전체 포트폴리오)

```python
@dataclass
class RebalancePlan:
    portfolio_id: str
    timestamp: datetime
    
    # 포트폴리오 스냅샷
    portfolio_snapshot: PortfolioSnapshot = None
    
    # 리밸런싱 판단
    should_rebalance: bool = False      # 실행 여부
    rebalance_reason: str = ""          # 이유 (BAND, CALENDAR 등)
    
    # 주문 목록
    orders: List[RebalanceOrder] = field(default_factory=list)
    
    # 통계
    total_delta_value: float = 0.0      # 총 변화 금액
    total_orders: int = 0               # 총 주문 수
```

**사용 예:**
```python
plan = RebalancePlan(
    portfolio_id="portfolio-001",
    timestamp=datetime.now(),
    portfolio_snapshot=snapshot,
    should_rebalance=True,
    rebalance_reason="BAND breach for ticker 005930",
    orders=[order1, order2],  # 여러 주문
    total_delta_value=2500000.0,
    total_orders=2
)

print(f"Rebalance needed: {plan.should_rebalance}")
print(f"Reason: {plan.rebalance_reason}")
for order in plan.orders:
    print(f"  {order.action} {order.ticker}: {order.delta_value:.0f} KRW")
```

### 6. ExecutionResult
리밸런싱 실행 결과

```python
@dataclass
class ExecutionResult:
    portfolio_id: str
    timestamp: datetime
    plan: RebalancePlan = None
    
    # 실행 상태
    succeeded: bool = False
    error_message: str = ""
    
    # 실행 주문들
    executed_orders: List[Dict] = field(default_factory=list)
    
    # 실행 후 포트폴리오
    post_portfolio_snapshot: PortfolioSnapshot = None
```

**사용 예:**
```python
result = ExecutionResult(
    portfolio_id="portfolio-001",
    timestamp=datetime.now(),
    plan=plan,
    succeeded=True,
    executed_orders=[
        {
            "ticker": "005930",
            "action": "buy",
            "status": "completed",
            "order_id": "ORD001"
        }
    ],
    post_portfolio_snapshot=updated_snapshot
)
```

## 사용 흐름

### 1. 포트폴리오 스냅샷 생성
```python
from modules.kis_portfolio_fetcher import KISPortfolioFetcher

fetcher = KISPortfolioFetcher(kis_auth)
snapshot = fetcher.fetch_portfolio_snapshot("portfolio-001")
```

### 2. 리밸런싱 계획 생성
```python
from modules.rebalancing_engine import RebalancingEngine

engine = RebalancingEngine(config)
plan = engine.create_rebalance_plan(snapshot)
```

### 3. 리밸런싱 실행
```python
from modules.order_executor import OrderExecutor

executor = OrderExecutor(config, kis_auth)
result = executor.execute_plan(plan)
```

## 데이터 모델 관계도

```
PortfolioSnapshot (포트폴리오 전체 상태)
  ├── cash: 현금
  ├── positions: Dict[str, PositionSnapshot]
  │   └── PositionSnapshot (각 종목의 보유 상황)
  │       └── ticker, quantity, price, evaluation
  └── total_value, stocks_value (계산된 값)

RebalancePlan (리밸런싱 계획)
  ├── portfolio_snapshot: PortfolioSnapshot
  ├── should_rebalance: bool
  ├── orders: List[RebalanceOrder]
  │   └── RebalanceOrder (각 종목별 주문)
  │       ├── ticker, action, delta_value
  │       └── estimated_quantity, estimated_price
  └── 통계 정보

ExecutionResult (실행 결과)
  ├── plan: RebalancePlan
  ├── executed_orders: List[Dict]
  └── post_portfolio_snapshot: PortfolioSnapshot
```

## 주의사항

1. **PortfolioSnapshot.positions**: Dict이므로 ticker 존재 여부를 먼저 확인해야 함
2. **evaluation 계산**: PositionSnapshot과 RebalanceOrder에서 자동으로 계산됨
3. **타임스탬프**: 모든 스냅샷에 기록되므로 시간 순서 추적 가능
4. **불변성**: dataclass는 frozen=False이므로 필요시 수정 가능하지만 권장하지 않음

## 타입 힌트

모든 모델은 타입 힌트를 제공하므로 IDE에서 자동완성과 타입 검사를 활용할 수 있습니다:

```python
def process_snapshot(snapshot: PortfolioSnapshot) -> RebalancePlan:
    # IDE가 snapshot의 메서드와 속성을 자동완성
    ...
```

---

## 변경 이력

### 2026-03-10: PositionSnapshot JSON 직렬화 지원 추가

**문제**: DB 저장 시 `Object of type PositionSnapshot is not JSON serializable` 에러 발생

**원인**: `PortfolioSnapshot.positions`가 `Dict[str, PositionSnapshot]` 타입인데, `PositionSnapshot` dataclass에 JSON 직렬화 메서드가 없었음

**해결**: `PositionSnapshot`에 `to_dict()` 메서드 추가

```python
@dataclass
class PositionSnapshot:
    # ... 기존 필드들 ...
    
    def to_dict(self) -> Dict:
        """객체를 JSON 직렬화 가능한 dict로 변환"""
        return {
            "ticker": self.ticker,
            "quantity": self.quantity,
            "price": self.price,
            "evaluation": self.evaluation
        }
```

**영향**: 이제 `PositionSnapshot` 객체를 DB에 저장할 때 정상적으로 JSON으로 변환됨
