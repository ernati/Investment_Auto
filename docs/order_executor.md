# Order Executor Module (order_executor.py)

## 개요
리밸런싱 계획을 실제 주문으로 변환하여 KIS API를 통해 실행하는 모듈입니다.
국내주식, 해외주식(SPY 등), 비트코인 주문을 모두 지원합니다.

## 리팩토링 이력

**v1.5 (Overseas Market Hours Check - 2026-04-01)**:
- **해외 시장 시간 체크 기능 추가**
- `market_hours` 모듈 연동 (`is_overseas_market_open`, `get_overseas_market_status`)
- 해외 시장 휴장 시 주문 스킵 처리 (에러 발생 방지)
- 스킵된 주문 로깅 및 결과 기록 기능

**v1.4 (Overseas Stock Support - 2026-03-30)**:
- **해외주식 주문 지원 추가** (SPY, AAPL 등 미국/홍콩/일본 주식)
- `KISOverseasTrading` 모듈 통합
- `RebalanceOrder.exchange` 필드를 통한 국내/해외주식 구분
- `_execute_overseas_order()` 메서드 추가 (해외주식 전용)
- `_execute_domestic_order()` 메서드 분리 (국내주식 전용)
- 해외주식 모의투자 지정가 주문 지원 (모의투자 제약 사항)

**v1.3 (KISTrading Integration - 2026-02-16)**:
- KISTrading 모듈 직접 사용으로 변경
- `kis_api_utils.place_stock_order()` → `KISTrading` 클래스 메서드 사용
- 시장가/지정가 주문 분기 로직 추가
- TR_ID 처리 개선 (VTTC0012U/VTTC0011U 사용)
- 에러 처리 강화 (RT_CD=1 문제 해결)

**v1.2 (Dry-Run Removal)**:
- Dry-run 모드 제거 (설정 파일의 real/demo 계좌로 대체)
- `_execute_order_dryrun()` 메서드 제거
- `dry_run` 설정 변수 제거
- 실전 주문 실행 로직 단순화 (분기문 제거)
- 코드 복잡도 감소 (순환 복잡도 개선)

**v1.1 (Refactoring Release)**:
- `kis_api_utils.py` 모듈의 공유 유틸리티 함수 사용으로 리팩토링
- 중복 코드 제거: `_get_headers()` 메서드 제거
- 주문 함수 통합: `_place_market_order()` 및 `_place_limit_order()` → `kis_api_utils.place_stock_order()`
- 코드 라인 수 감소 (~30% 축소, 294행 → 165행)
- 에러 처리 로직 표준화로 유지보수성 향상

## 주요 기능

### 1. 실전 주문 실행
```
KIS API를 통해 실제 주문 발생
→ 포트폴리오 자동 관리
```

### 2. 주문 순서 관리
```
매도 → 매수 순서 (현금 확보)
```

### 3. 주문 타입 지원
```
- 시장가 주문 (Market Order)
- 지정가 주문 (Limit Order, 선택)
```

## 클래스 설명

### OrderExecutor

#### 생성자
```python
OrderExecutor(
    config_loader: PortfolioConfigLoader,
    kis_auth: KISAuth
)
```

#### 속성

| 속성 | 설명 |
|------|------|
| `config` | 설정 로더 |
| `kis_auth` | KIS 인증 정보 |
| `order_type` | market 또는 limit |

#### 메서드

##### execute_plan(plan)
리밸런싱 계획을 실행합니다.

**Parameters:**
- `plan` (RebalancePlan): 리밸런싱 계획

**Returns:**
- `ExecutionResult`: 실행 결과

**Process:**
1. 리밸런싱 필요 여부 확인
2. 매도 주문 실행 (먼저)
3. 매수 주문 실행 (나중)
4. 결과 수집

**예시:**
```python
config = get_portfolio_config()
executor = OrderExecutor(config, kis_auth)

result = executor.execute_plan(plan)
if result.succeeded:
    print(f"✅ 주문 실행 성공: {len(result.executed_orders)}개 주문")
    for order in result.executed_orders:
        print(f"  {order['ticker']}: {order['action']}")
else:
    print(f"❌ 주문 실행 실패: {result.error_message}")
```

---

##### _place_market_order(order) (내부)
시장가 주문을 건다.

**Parameters:**
- `order` (RebalanceOrder): 주문 정보

**Returns:**
```python
{
    'success': bool,
    'message': str,
    'order_id': str,  # 성공 시에만
    'ticker': str,
    'action': str
}
```

---

##### _execute_overseas_order(order) (내부)
해외주식 주문을 실행합니다.

**Parameters:**
- `order` (RebalanceOrder): 주문 정보 (exchange 필드 필수)

**Returns:**
```python
{
    'success': bool,
    'order_no': str,
    'message': str,
    'symbol': str,
    'side': str,
    'quantity': int,
    'price': float
}
```

**Note:**
- 해외주식 모의투자는 **지정가 주문만 지원**합니다.
- 지원 거래소: NASD(나스닥), NYSE(뉴욕), AMEX, SEHK(홍콩), TKSE(일본) 등

---

##### _execute_domestic_order(order) (내부)
국내주식 주문을 실행합니다.

**Parameters:**
- `order` (RebalanceOrder): 주문 정보

**Returns:**
- 시장가/지정가 주문 결과

---

##### _place_limit_order(order) (내부)
지정가 주문을 건다.

**Parameters:**
- `order` (RebalanceOrder): 주문 정보 (가격 포함)

**Returns:**
```python
{
    'success': bool,
    'message': str,
    'order_id': str,  # 성공 시에만
    'ticker': str,
    'action': str
}
```

## 설정

### config_advanced.json
```json
{
  "order_policy": {
    "order_type": "market"
  }
}
```
- `market`: 시장가 주문 (권장)
- `limit`: 지정가 주문 (선택)

### 실전 vs 모의투자
테스트 목적으로 모의투자를 사용하려면:
```python
# config.json에서 demo 계좌 설정
kis_config = config.get_kis_config('demo')

# 또는 kis_app_utils 함수에서 명시적으로 지정
api_client, trading, _ = setup_kis_trading_client('demo')
```

## 실행 흐름

```
RebalancePlan
   ↓
[KIS API: 매도 주문들 실행]
   ↓
[KIS API: 매수 주문들 실행]
   ↓
ExecutionResult (실행 주문 목록)
   ↓
포트폴리오 변경됨
```

## 주문 실행 순서

반드시 **매도 → 매수** 순서 (현금 확보를 위해):

```python
# 1. 매도 주문 먼저
sell_orders = [o for o in plan.orders if o.action == "sell"]
for order in sell_orders:
    _execute_order_live(order)

# 2. 매수 주문 (확보한 현금으로)
buy_orders = [o for o in plan.orders if o.action == "buy"]
for order in buy_orders:
    _execute_order_live(order)
```

**이유:**
- 현금 부족으로 인한 매수 실패 방지
- 신용 거래 없이 안전하게 실행

## 사용 패턴

### 패턴 1: 실전 모드 실행
```python
config = get_portfolio_config()

# 1. 설정 검증
validator = ConfigValidator(config)
success, errors, _ = validator.validate()
if not success:
    raise RuntimeError("Configuration validation failed")

# 2. 리밸런싱 계획 생성
plan = engine.create_rebalance_plan(snapshot)
passed, _ = engine.check_guardrails(plan)
if not passed:
    raise RuntimeError("Guardrail check failed")

# 3. 실행
executor = OrderExecutor(config, kis_auth)
result = executor.execute_plan(plan)

if result.succeeded:
    print("✅ 주문 실행 성공")
else:
    print(f"❌ 주문 실행 실패: {result.error_message}")
```

### 패턴 3: 에러 처리
```python
try:
    result = executor.execute_plan(plan)
except RequestException as e:
    logger.error(f"네트워크 오류: {e}")
except RuntimeError as e:
    logger.error(f"주문 실패: {e}")
```

## 실행 결과 (ExecutionResult)

### 성공 시
```python
result.succeeded = True
result.executed_orders = [
    {
        'ticker': '005930',
        'action': 'sell',
        'order_id': 'ORD001',
        'status': 'completed',
        'timestamp': '2025-02-08T10:00:00'
    },
    {
        'ticker': '005930',
        'action': 'buy',
        'order_id': 'ORD002',
        'status': 'completed',
        'timestamp': '2025-02-08T10:01:00'
    }
]
```

### 실패 시
```python
result.succeeded = False
result.error_message = "Order placement failed: 계좌번호 오류"
result.executed_orders = [...]  # 부분 실행된 주문들
```

## API 엔드포인트

### 사용하는 KIS API

| 주문 타입 | 엔드포인트 | TR ID |
|----------|-----------|-------|
| 시장가/지정가 | `/uapi/domestic-stock/v1/trading/order-cash` | TTTC0802U/TTTC0801U |

## 에러 처리

### API 호출 실패
```python
try:
    result = executor.execute_plan(plan)
except RequestException as e:
    logger.error(f"API 호출 실패: {e}")
    # 네트워크 재시도 로직 추가 가능
```

### 부분 실패
```python
if result.succeeded:
    print(f"✅ 모든 주문 성공")
else:
    print(f"❌ 일부 주문 실패")
    for order in result.executed_orders:
        if order.get('status') == 'failed':
            print(f"   - {order['ticker']}: {order['message']}")
```

## 주의사항

### 1. API 호출 제한
```
한국투자증권 API는 호출 빈도 제한이 있음
- 초당 호출 수 제한
- 일일 호출 횟수 제한 (확인 필수)
```

### 2. 매도 → 매수 순서
```
반드시 이 순서를 지킬 것
- 역순 시 현금 부족으로 매수 실패 가능
- 신용 거래 없을 추가 비용 발생 가능
```

### 3. 토큰 관리
```
KIS API 호출 시 토큰이 자동으로 갱신됨
- 만료되면 자동 재발급
- 6시간마다 새 토큰 발급 권장
```

### 4. 확인해야 할 사항
```
- 계좌번호: 8자리 숫자 정확해야 함
- 상품코드: "01" (주식) 확인
- 종목코드: 6자리 코드 정확해야 함
- 수량: 양수 정수만 가능
- 금액: 최소 주문금액 이상
```

### 5. 수량 0 주문 스킵
```
계산된 수량이 0 이하이면 주문을 실행하지 않음
```

## 성능

- 단일 주문: ~0.5초
- N개 주문: ~0.5 + (N-1)×0.1 초 (순차 처리)
- 전체 프로세스: 매도 개수 + 매수 개수 만큼

## 로깅

Logger: `modules.order_executor`

```
"Executing sell order for 005930: qty=100, price=70000.0"
"Skipping buy order for 005930: quantity=0"
"Order placed successfully: {'order_id': 'ORD001', ...}"
"Request error placing market order: Connection timeout"
```

## 참고: 실제 환경 구성

실전 모드 사용 시 필수 구성:

```python
# 1. 설정 파일 검증
validator = ConfigValidator(config)
if not validator.validate()[0]:
    raise RuntimeError("설정 검증 실패")

# 2. KIS API 테스트
auth = KISAuth(...)
fetcher = KISPortfolioFetcher(auth)
snapshot = fetcher.fetch_portfolio_snapshot("portfolio-001")

# 3. 리밸런싱 검증
engine = RebalancingEngine(config)
plan = engine.create_rebalance_plan(snapshot)
passed, _ = engine.check_guardrails(plan)

# 4. 실행 (모든 검증 통과 후)
executor = OrderExecutor(config, auth)
result = executor.execute_plan(plan)
```

## 변경 이력

### v1.5 (2026-04-01) - 해외 시장 시간 체크 기능 추가

**문제점:**
- 한국 장 시간(09:00~15:30)에 해외주식(SPY 등) 주문 시도 시 API 에러 발생
- 에러 코드: `40580000` (장종료), `40570000` (장시작전)

**해결책:**
- `market_hours.py` 모듈의 해외 시장 시간 체크 함수 사용
- `_execute_overseas_order()` 메서드에서 주문 전 시장 시간 체크
- 시장 휴장 시 에러 없이 스킵 처리

**수정 내용:**
1. `market_hours` 모듈 import 추가
   ```python
   from .market_hours import is_overseas_market_open, get_overseas_market_status, format_market_status
   ```

2. `_execute_overseas_order()` 메서드에 시장 시간 체크 로직 추가
   ```python
   if order.exchange:
       market_status = get_overseas_market_status(order.exchange)
       if not market_status.is_open:
           logger.warning(f"Overseas market closed, skipping order...")
           return {"success": False, "skipped": True, "market_closed": True, ...}
   ```

3. `_execute_order_live()` 메서드에서 스킵된 주문 처리
   ```python
   if order_result.get("skipped") and order_result.get("market_closed"):
       logger.info(f"Skipped overseas order: market closed")
       return  # 에러 없이 다음 주문으로 진행
   ```

**동작 방식:**
- 해외주식 주문 시 해당 거래소 시장 시간 확인
- 시장 휴장 시: 경고 로그 출력 후 스킵 (에러 발생하지 않음)
- 시장 개장 시: 정상적으로 주문 실행

**지원 거래소 및 시간:**
| 거래소 | 시간대 | 장 시간 |
|--------|--------|---------|
| NYSE, NASD, AMEX | America/New_York | 09:30~16:00 |
| SEHK (홍콩) | Asia/Hong_Kong | 09:30~16:00 |
| TKSE (일본) | Asia/Tokyo | 09:00~15:00 |

### v1.4 (2026-03-30)
- 해외주식 주문 지원 추가 (SPY, AAPL 등)

### v1.3 (2026-02-16)
- KISTrading 모듈 직접 사용으로 변경

### v1.2
- Dry-run 모드 제거

### v1.1
- `kis_api_utils.py` 모듈 사용으로 리팩토링
