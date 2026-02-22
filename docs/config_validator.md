# Config Validator Module (config_validator.py)

## 개요
포트폴리오 리밸런싱 설정을 검증하는 모듈입니다.
설계서에서 정의한 모든 검증 규칙을 확인합니다.

## 주요 기능

### 1. 필수 필드 검증
- `BASIC:/portfolio_id`: 포트폴리오 ID
- `BASIC:/base_currency`: 기본 통화
- `BASIC:/target_weights`: 목표 비중

### 2. 설정 값 범위 검증
- 목표 비중 합계: 1.0
- 현금 버퍼 비율: 0~1
- 밴드 값: 음수 불가
- 최소 주문금액: 음수 불가

### 3. 리밸런싱 설정 검증
- 모드: BAND, CALENDAR, HYBRID 중 하나
- 가격 출처: close 또는 last
- Ban d 설정 (필요시): type, value

### 4. 스케줄 설정 검증
- 타임존 존재
- hourly 또는 run_times 설정 (둘 다 없으면 경고)

### 5. 실전 모드 검증
- `kis/env = real` AND `dry_run = false`이면 ADV:/integrations/broker 필수

## 클래스 설명

### ConfigValidator

#### 생성자
```python
ConfigValidator(config_loader: PortfolioConfigLoader)
```

#### 메서드

##### validate()
전체 설정을 검증합니다.

**Returns:**
```python
(
    success: bool,           # 성공 여부
    errors: List[str],       # 에러 메시지
    warnings: List[str]      # 경고 메시지
)
```

**Example:**
```python
validator = ConfigValidator(config)
success, errors, warnings = validator.validate()

if not success:
    print("❌ 설정 검증 실패:")
    for error in errors:
        print(f"  - {error}")

if warnings:
    print("⚠️ 경고:")
    for warning in warnings:
        print(f"  - {warning}")
```

---

##### print_report()
검증 결과를 보기 좋게 출력합니다.

**Example:**
```python
validator = ConfigValidator(config)
validator.validate()
validator.print_report()

# Output:
# ============================================================
# Configuration Validation Report
# ============================================================
# 
# ❌ ERRORS (2):
#   1. BASIC:/target_weights: Sum must be 1.0, got 0.900000
#   2. ADV:/integrations/broker/provider: Must be configured...
#
# ⚠️  WARNINGS (1):
#   1. BASIC:/rebalance/schedule: Both hourly and run_times...
# 
# ============================================================
```

## 검증 규칙

### Rule 1: 필수 필드
```
BASIC:/portfolio_id - 필수
BASIC:/base_currency - 필수
BASIC:/target_weights - 필수 및 비어있지 않음
```

### Rule 2: 목표 비중
```
- 모든 비중은 0 이상 1 이하
- 비중의 합계는 1.0 (소수점 6자리까지)
- 예: 0.50 + 0.30 + 0.20 = 1.0 ✅
- 예: 0.50 + 0.30 + 0.15 = 0.95 ❌
```

**에러 메시지:**
```
BASIC:/target_weights: Sum must be 1.0, got 0.900000
BASIC:/target_weights/005930: Weight must be between 0 and 1
```

### Rule 3: 리밸런싱 모드
```
mode ∈ {"BAND", "CALENDAR", "HYBRID"}
```

**에러 메시지:**
```
BASIC:/rebalance/mode: Must be 'BAND', 'CALENDAR', or 'HYBRID', got 'INVALID'
```

### Rule 4: 밴드 설정 (BAND 또는 HYBRID 모드)
```
band.type ∈ {"ABS", "REL"}
band.value ≥ 0
```

**에러 메시지:**
```
BASIC:/rebalance/band/type: Must be 'ABS' or 'REL', got 'PCT'
BASIC:/rebalance/band/value: Must be non-negative, got -0.05
```

### Rule 5: 가격 출처
```
price_source ∈ {"close", "last"}
```

**에러 메시지:**
```
BASIC:/rebalance/price_source: Must be 'close' or 'last', got 'mid'
```

### Rule 6: 거래 설정
```
cash_buffer_ratio ∈ [0, 1]
min_order_krw ≥ 0 (정수)
```

**에러 메시지:**
```
BASIC:/trade/cash_buffer_ratio: Must be between 0 and 1, got 1.5
BASIC:/trade/min_order_krw: Must be non-negative integer, got -100000
```

### Rule 7: 스케줄 설정
```
timezone - 필수 (유효한 타임존)
hourly enabled=false AND run_times=[] → 경고
```

**에러 메시지:**
```
BASIC:/rebalance/schedule/timezone: Missing timezone
```

**경고 메시지:**
```
BASIC:/rebalance/schedule: Both hourly and run_times are disabled/empty.
  Rebalancing will never be triggered.
```

### Rule 8: 실전 모드 (kis/env=real AND dry_run=false)
```
ADV:/integrations/broker/provider - 필수
ADV:/integrations/broker/account_id - 권장
```

**에러 메시지:**
```
ADV:/integrations/broker/provider: Must be configured for LIVE mode
```

**경고 메시지:**
```
ADV:/integrations/broker/account_id: Verify account_id is correctly configured
```

## 사용 패턴

### 패턴 1: 애플리케이션 시작 시 검증
```python
from modules.config_loader import get_portfolio_config
from modules.config_validator import ConfigValidator

config = get_portfolio_config()

# 검증
validator = ConfigValidator(config)
success, errors, warnings = validator.validate()

if not success:
    print("설정 검증 실패, 애플리케이션 종료")
    exit(1)

# 경고 확인
if warnings:
    print(f"⚠️ {len(warnings)}개 경고가 있습니다")

# 정상 진행
print("✅ 설정 검증 완료")
```

### 패턴 2: 상세 리포트 출력
```python
validator = ConfigValidator(config)
validator.validate()
validator.print_report()

# 터미널에 예쁘게 출력됨
```

### 패턴 3: 실전 모드 전환 전 검증
```python
# 개발 중: dry_run = true
# config_basic.json 업데이트 후 실전 모드로 전환 시:

config = get_portfolio_config(reload=True)  # 최신 설정 로드
validator = ConfigValidator(config)

success, errors, warnings = validator.validate()

if not success:
    print("❌ 설정 오류:")
    for error in errors:
        print(f"  {error}")
    return False

if "dry_run" in config.get_basic("dry_run", True):
    print("❌ dry_run이 false로 설정되지 않았습니다")
    return False

print("✅ 실전 모드 진입 준비 완료")
return True
```

## 에러 vs 경고

### 에러 (반드시 해결)
- 필수 설정 누락
- 값 범위 벗어남
- 타입 오류
- 실전 모드 필수 설정 누락

**→ validate() 반환 success=False**

### 경고 (확인 권장)
- 리밸런싱이 절대 실행되지 않을 설정
- 실전 모드에서 계좌 번호 확인 권장
- 설정값이 일반적이지 않음

**→ validate() 반환 success=True (경고만 있는 경우)**

## 검증 흐름

```
ConfigValidator 생성
  ↓
validate() 호출
  ├─ 필수 필드 확인
  ├─ 목표 비중 확인
  ├─ 리밸런싱 설정 확인
  ├─ 거래 설정 확인
  ├─ 스케줄 설정 확인
  └─ 실전 모드 설정 확인
  ↓
(errors, warnings 수집)
  ↓
로깅 & 반환
```

## 실제 검증 예시

### 예시 1: 목표 비중 합계 오류
```python
# config_basic.json
{
  "target_weights": {
    "005930": 0.50,
    "000660": 0.30,
    "035420": 0.15  # ❌ 합계 = 0.95
  }
}

# 결과
errors = [
    "BASIC:/target_weights: Sum must be 1.0, got 0.950000"
]
```

### 예시 2: 스케줄 설정 누락
```python
# config_basic.json
{
  "rebalance": {
    "schedule": {
      "timezone": "Asia/Seoul",
      "run_times": [],  # ❌ 비어있음
      "calendar_rules": {
        "hourly": {
          "enabled": false  # ❌ disabled
        }
      }
    }
  }
}

# 결과
warnings = [
    "BASIC:/rebalance/schedule: Both hourly and run_times are disabled..."
]
```

### 예시 3: 실전 모드 미설정
```python
# config_basic.json
{
  "dry_run": false  # 실전 모드
}

# config_advanced.json
{
  "integrations": {
    "broker": {
      "provider": "YOUR_BROKER_PROVIDER",  # ❌ 미변경
      "account_id": "ACCOUNT-001"         # ❌ 미변경
    }
  }
}

# 결과
errors = [
    "ADV:/integrations/broker/provider: Must be configured for LIVE mode"
]
warnings = [
    "ADV:/integrations/broker/account_id: Verify account_id..."
]
```

## 주의사항

1. **검증은 논리 검사만 수행**
   - KIS API 연결성 검사 안 함
   - 계좌 번호 존재 여부 검사 안 함
   - → 실행 시점에 발견 가능

2. **부동소수점 비교**
   - 합계 비교: 소수점 6자리까지 허용
   - 부동소수점 오차 고려

3. **타임존 검증**
   - 유효하지 않은 타임존도 로더에서 자동 처리
   - 경고는 기록하지 않음

4. **검증 순서**
   - 모든 에러를 수집 후 반환 (partial failure 없음)
   - 첫 번째 에러에서 중단하지 않음

## 로깅

Logger: `modules.config_validator`

```python
import logging

logger = logging.getLogger("modules.config_validator")
logger.setLevel(logging.INFO)

# 검증 결과 로깅
# "INFO - All validations passed"
# "ERROR - Validation failed with 2 errors"
# "WARNING - There are 1 warnings"
```

## 성능

- 검증 시간: ~1ms (설정 크기 작음)
- 메모리: 무시할 수 있는 수준
- 실행 시간: 비동기 불필요
