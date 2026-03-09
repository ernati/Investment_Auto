# Rebalancing Engine Module (rebalancing_engine.py)

## 개요
포트폴리오 상태를 분석하고 리밸런싱 계획을 수립하는 핵심 엔진입니다.
- 리밸런싱 필요 여부 판단 (BAND, CALENDAR, HYBRID)
- 주문 계획 자동 생성
- 가드레일(위험 제어) 검사

## 주요 기능

### 1. 리밸런싱 필요 여부 판단

#### BAND 모드
밴드(허용 범위)를 벗어나면 리밸런싱 실행
```
목표 비중 ± 밴드 범위를 벗어남 → 리밸런싱 필요
```

#### CALENDAR 모드
캘린더 규칙으로 트리거될 때만 실행

#### HYBRID 모드
**BAND 조건 OR CALENDAR 조건 중 하나라도 만족** → 리밸런싱 실행

### 2. 주문 계획 생성
```
- 현재 포트폴리오 평가액 분석
- 목표 비중과 비교
- 필요한 매수/매도 금액 계산
- 최소 주문금액(min_order_krw) 미만은 스킵
```

### 3. 가드레일 검사
리밸런싱 계획이 위험 제어 조건을 만족하는지 검증:
- 최대 회전율 (turnover)
- 최대 주문 개수
- 단일 주문 최대 금액

## 클래스 설명

### RebalancingEngine

#### 생성자
```python
RebalancingEngine(config_loader: PortfolioConfigLoader)
```

#### 속성

| 속성 | 설명 |
|------|------|
| `portfolio_id` | 포트폴리오 ID |
| `target_weights` | 목표 비중 딕셔너리 |
| `rebalance_mode` | BAND, CALENDAR, HYBRID |
| `band_type` | ABS(절대) 또는 REL(상대) |
| `band_value` | 밴드 값 |
| `cash_buffer_ratio` | 현금 버퍼 비율 |
| `min_order_krw` | 최소 주문금액 |

#### 메서드

##### create_rebalance_plan(portfolio_snapshot, is_calendar_triggered)
리밸런싱 계획을 생성합니다.

**Parameters:**
- `portfolio_snapshot` (PortfolioSnapshot): 포트폴리오 현황
- `is_calendar_triggered` (bool): 캘린더 규칙 트리거 여부

**Returns:**
- `RebalancePlan`: 리밸런싱 계획

**Logic:**
1. 리밸런싱 필요 여부 판단
2. 필요하면 주문 계획 생성
3. 가드레일 검사는 별도로 수행

**예시:**
```python
engine = RebalancingEngine(config)
snapshot = fetcher.fetch_portfolio_snapshot("portfolio-001")

plan = engine.create_rebalance_plan(
    portfolio_snapshot=snapshot,
    is_calendar_triggered=False
)

if plan.should_rebalance:
    print(f"Reason: {plan.rebalance_reason}")
    print(f"Orders: {plan.total_orders}")
else:
    print("No rebalancing needed")
```

---

##### check_guardrails(plan)
리밸런싱 계획이 위험 가드레일을 통과하는지 검사합니다.
(하위 호환성을 위해 유지, **apply_guardrails 사용 권장**)

**Parameters:**
- `plan` (RebalancePlan): 리밸런싱 계획

**Returns:**
- `(passed, message)`: (통과 여부, 메시지)

**검사 항목:**
- `max_turnover_per_run`: 회전율이 초과되지 않은가?
- `max_orders_per_run`: 주문 개수가 초과되지 않은가?
- `max_single_order_krw`: 단일 주문이 초과되지 않은가?

---

##### apply_guardrails(plan) ✨ NEW
가드레일을 적용하여 주문을 **점진적으로 조정**합니다.
기존 `check_guardrails`와 달리, 한도 초과 시 **스킵하지 않고 한도 내에서 실행**합니다.

**Parameters:**
- `plan` (RebalancePlan): 원본 리밸런싱 계획

**Returns:**
- `(adjusted_plan, message)`: (조정된 계획, 메시지)

**조정 로직:**

| 가드레일 | 초과 시 동작 |
|---------|-------------|
| `max_single_order_krw` | 해당 주문을 한도 금액 내로 수량 축소 |
| `max_orders_per_run` | delta_value가 큰 주문 우선 선택, 나머지 제외 |
| `max_turnover_per_run` | 모든 주문을 비례적으로 축소 |

**Why 점진적 조정?**
- 기존: 한도 초과 → 전체 리밸런싱 스킵
- 문제: 목표 비중과 크게 다른 경우 **영원히 리밸런싱 불가**
- 해결: 한도 내에서 **매 실행마다 조금씩 목표에 접근**

**예시:**
```python
# 원본 계획: 단일 주문 1,000만원 (한도 500만원 초과)
plan = engine.create_rebalance_plan(snapshot)  

# 조정된 계획: 단일 주문 500만원으로 축소
adjusted_plan, message = engine.apply_guardrails(plan)

if adjusted_plan.total_orders > 0:
    # 점진적으로 목표 비중에 접근
    result = executor.execute_plan(adjusted_plan)
```

**조정 순서:**
1. 단일 주문 금액 조정 (`max_single_order_krw`)
2. 주문 개수 조정 (`max_orders_per_run`)
3. Turnover 조정 (`max_turnover_per_run`)
4. `min_order_krw` 미만 주문 제거

**예시:**
```python
passed, message = engine.check_guardrails(plan)
if not passed:
    print(f"❌ Guardrail failed: {message}")
    # 리밸런싱 실행 취소
else:
    print(f"✅ {message}")
    # 리밸런싱 실행
```

## 밴드(Band) 이해

### 절대값 밴드 (ABS)
```
목표 비중 ± 밴드값
예: target = 0.5, band = 0.05
범위: [0.45, 0.55]
현재 비중이 0.45 미만이거나 0.55 초과 → 리밸런싱
```

### 상대값 밴드 (REL)
```
목표 비중 × (1 ± 밴드값)
예: target = 0.5, band = 0.1 (10%)
범위: [0.45, 0.55]  (0.5 × 0.9 ~ 0.5 × 1.1)
```

### 밴드 설정 예시

#### 엄격한 관리 (5% ABS)
```json
{
  "band": {
    "type": "ABS",
    "value": 0.05
  }
}
```
→ 목표 비중에서 ±5% 내에만 허용

#### 유연한 관리 (20% REL)
```json
{
  "band": {
    "type": "REL",
    "value": 0.2
  }
}
```
→ 목표 비중의 80%~120% 범위 허용

## 주문 생성 로직

### Step 1: 사용 가능 자산 계산
```python
사용 가능 총액 = 총평가액 × (1 - 현금버퍼비율)
예: 10,000,000원 × (1 - 0.02) = 9,800,000원
```

### Step 2: 종목별 목표 금액 계산
```python
목표금액 = 사용가능총액 × 목표비중
예: 9,800,000 × 0.5 = 4,900,000 (50%)
```

### Step 3: 필요 변화량 계산
```python
필요변화량 = 목표금액 - 현재금액
양수 → 매수 (buy)
음수 → 매도 (sell)
```

### Step 4: 최소 주문금액 검사
```python
|필요변화량| < min_order_krw → 스킵
```

### Step 5: 가격/수량 유효성 검사
```python
가격 <= 0 → 스킵
계산된 수량 <= 0 → 스킵
```

### 주문 생성 예시

설정:
- 목표 비중: 삼성전자 50%, SK하이닉스 30%, NAVER 20%
- 총 평가액: 10,000,000원
- 현금 버퍼: 2%
- 최소 주문: 100,000원

현황:
- 현금: 1,000,000원
- 삼성전자: 500주 × 70,000 = 35,000,000원 (350%)
- SK하이닉스: 100주 × 60,000 = 6,000,000원 (60%)

결과:
```
사용 가능: 10,000,000 × (1-0.02) = 9,800,000

삼성전자:
  목표: 9,800,000 × 0.50 = 4,900,000
  현재: 35,000,000
  변화: 4,900,000 - 35,000,000 = -30,100,000 (매도)

SK하이닉스:
  목표: 9,800,000 × 0.30 = 2,940,000
  현재: 6,000,000
  변화: 2,940,000 - 6,000,000 = -3,060,000 (매도)

NAVER:
  목표: 9,800,000 × 0.20 = 1,960,000
  현재: 0
  변화: 1,960,000 - 0 = 1,960,000 (매수)
```

## 가드레일 설정

### config_advanced.json 예시
```json
{
  "risk_guardrails": {
    "max_turnover_per_run": 0.1,
    "max_orders_per_run": 30,
    "max_single_order_krw": 5000000
  }
}
```

### 각 항목 설명

#### max_turnover_per_run
총 변화 금액이 포트폴리오의 10% 이상이면 **조정**
```
총 변화 = |매도| + |매수| (합계)
회전율 = 총 변화 / 총 평가액
0.1 (10%) 초과 → 비례적으로 모든 주문 축소
```

#### max_orders_per_run
한 번의 리밸런싱에서 최대 30개 주문까지만 허용
```
주문 개수 > 30 → delta_value가 큰 주문 30개만 선택
```

#### max_single_order_krw
단일 주문이 5,000,000원을 초과하면 **조정**
```
각 주문 금액 > 5,000,000 → 해당 주문을 5,000,000원 이하로 축소
```

### 점진적 조정 예시

**시나리오:** 포트폴리오 초기 설정이 목표와 크게 다름
- 현재 비중: 삼성전자 80%
- 목표 비중: 삼성전자 40%
- `max_single_order_krw`: 500만원

**기존 방식 (check_guardrails):**
```
필요 매도: 4,000만원 > 한도 500만원
→ 전체 리밸런싱 스킵
→ 영원히 목표 비중 도달 불가 ❌
```

**새로운 방식 (apply_guardrails):**
```
1회차: 500만원 매도 (80% → 76%)
2회차: 500만원 매도 (76% → 72%)
...
N회차: 목표 비중 40% 도달 ✅
```

## 사용 흐름

### 권장: apply_guardrails 사용 (점진적 실행)
```python
# 1. 엔진 초기화
engine = RebalancingEngine(config)

# 2. 포트폴리오 스냅샷 조회
snapshot = fetcher.fetch_portfolio_snapshot("portfolio-001")

# 3. 리밸런싱 계획 생성
is_calendar = scheduler.is_execution_time()
plan = engine.create_rebalance_plan(
    portfolio_snapshot=snapshot,
    is_calendar_triggered=is_calendar
)

# 4. 가드레일 적용 (점진적 조정)
adjusted_plan, msg = engine.apply_guardrails(plan)
logger.info(f"Guardrails: {msg}")

if plan.should_rebalance and adjusted_plan.total_orders > 0:
    # 5. 조정된 계획으로 주문 실행
    result = executor.execute_plan(adjusted_plan)
```

### 기존: check_guardrails 사용 (스킵 방식)
```python
# 1. 엔진 초기화
engine = RebalancingEngine(config)

# 2. 포트폴리오 스냅샷 조회
snapshot = fetcher.fetch_portfolio_snapshot("portfolio-001")

# 3. 리밸런싱 계획 생성
is_calendar = scheduler.is_execution_time()
plan = engine.create_rebalance_plan(
    portfolio_snapshot=snapshot,
    is_calendar_triggered=is_calendar
)

# 4. 가드레일 검사 (초과 시 스킵)
passed, msg = engine.check_guardrails(plan)

if plan.should_rebalance and passed:
    # 5. 주문 실행
    result = executor.execute_plan(plan)
```

## 모드별 동작 비교

| 모드 | BAND 조건 | CALENDAR 조건 | 결과 |
|------|----------|--------------|------|
| BAND | O | X | ✅ 실행 |
| BAND | X | O | ❌ 스킵 |
| CALENDAR | O | X | ❌ 스킵 |
| CALENDAR | X | O | ✅ 실행 |
| HYBRID | O | X | ✅ 실행 |
| HYBRID | X | O | ✅ 실행 |
| HYBRID | O | O | ✅ 실행 |

## 로깅

Logger: `modules.rebalancing_engine`

```
"Band breach detected for 005930: current=0.35, target=0.50, band=[0.45, 0.55]"
"Order created for 005930: action=buy, delta_value=1500000.00"
"[Guardrail] 005930: 단일 주문 한도 적용 (100주 → 50주, 금액: 10,000,000원 → 5,000,000원)"
"[Guardrail] Turnover 한도 적용: 15.00% → 10.00% (scale: 66.67%)"
"[Guardrail Summary] 주문수: 5 → 3, 총거래금액: 15,000,000원 → 8,000,000원"
```

## 주의사항

1. **목표 비중 합계**: 반드시 1.0이어야 함 (검증 모듈에서 확인)
2. **현금 버퍼**: 긴급 자금으로 예약되므로 리밸런싱에서 제외
3. **최소 주문**: 너무 낮으면 많은 주문이 스킵될 수 있음
4. **밴드 타입**: ABS (절대값)이 더 직관적, REL (상대값)은 유연함
5. **가격 유효성**: 가격이 없거나 0이면 주문이 생성되지 않음
6. **가드레일**: 없으면 모든 계획이 통과 (주의)
7. **점진적 조정**: `apply_guardrails` 사용 시 여러 번 실행해야 목표 도달 가능

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-09 | `apply_guardrails` 메서드 추가 - 점진적 거래 지원 |
