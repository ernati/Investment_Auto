# Portfolio Scheduler Module (scheduler.py)

## 개요
설정 기반의 스케줄링을 관리하는 모듈입니다.
언제 리밸런싱을 측정하고 실행할지 결정합니다.

## 주요 기능

### 1. 스케줄 우선순위 지원
설계서에 정의된 우선순위 규칙:
- **Hourly 규칙 활성화 (enabled=true)**
  - Hourly 규칙만 사용 → run_times는 무시
  - 매시간 지정된 분에 실행
  
- **Hourly 규칙 비활성화 (enabled=false)**
  - run_times의 정해진 시각에 실행
  - 또는 calendar_rules 조건에 맞을 때 실행

### 2. 스케줄 규칙
- **Hourly**: 매시간의 특정 분에 실행 (테스트용)
- **Run Times**: 지정된 시각들 (HH:MM 형식)
- **Calendar Rules**: 월말, 분기말, 매주 특정 요일

### 3. 실행 횟수 제한
일일 최대 실행 횟수 제한 (ADV:/run_limit/max_runs_per_day)

### 4. 타임존 지원
BASIC:/rebalance/schedule/timezone 설정에 따른 타임존 처리

## 클래스 설명

### PortfolioScheduler

#### 생성자
```python
PortfolioScheduler(config_loader: PortfolioConfigLoader)
```

#### 속성

| 속성 | 설명 |
|------|------|
| `timezone` | Asia/Seoul 등 ZoneInfo 객체 |
| `hourly_enabled` | Hourly 규칙 활성화 여부 |
| `hourly_minute` | 매시간의 실행 분 |
| `run_times` | HH:MM 형식의 실행 시각 리스트 |
| `month_end` | 월말 실행 여부 |
| `quarter_end` | 분기말 실행 여부 |
| `weekly_enabled` | 주간 실행 여부 |
| `weekly_weekday` | 실행 요일 (MON, TUE, ..., SUN) |
| `max_runs_per_day` | 일일 최대 실행 횟수 |

#### 메서드

##### is_execution_time(current_time)
현재 시간이 리밸런싱 실행 시간인지 판단합니다.

**Parameters:**
- `current_time` (datetime, optional): 판단할 시간 (기본: 현재시간)

**Returns:**
- `bool`: 실행 시간이면 True

**Logic:**
1. 일일 실행 횟수 제한 확인
2. Hourly vs Run Times 우선순위 적용
3. Calendar Rules 확인

**예시:**
```python
scheduler = PortfolioScheduler(config)

# 현재 시간이 실행 시간인가?
if scheduler.is_execution_time():
    # 리밸런싱 실행
    ...
```

---

##### record_execution(execution_time)
리밸런싱 실행을 기록합니다 (일일 횟수 카운트).

**Parameters:**
- `execution_time` (datetime, optional): 실행 시간 (기본: 현재시간)

**사용:**
```python
# 리밸런싱 실행 후
scheduler.record_execution()

# 또는
scheduler.record_execution(execution_time=datetime.now())
```

---

##### get_next_execution_time(current_time)
다음 실행 예정 시간을 계산합니다 (근사값).

**Parameters:**
- `current_time` (datetime, optional): 기준 시간 (기본: 현재시간)

**Returns:**
- `datetime`: 다음 실행 예정 시간

**예시:**
```python
next_time = scheduler.get_next_execution_time()
print(f"다음 실행: {next_time.strftime('%Y-%m-%d %H:%M:%S')}")
```

## 설정 예시

### config_basic.json - Hourly 모드 (테스트용)
```json
{
  "rebalance": {
    "schedule": {
      "timezone": "Asia/Seoul",
      "run_times": [],
      "calendar_rules": {
        "hourly": {
          "enabled": true,
          "minute": 0
        }
      }
    }
  }
}
```
→ **매시간 00분에 실행** (10:00, 11:00, 12:00, ...)

### config_basic.json - Run Times 모드
```json
{
  "rebalance": {
    "schedule": {
      "timezone": "Asia/Seoul",
      "run_times": ["09:30", "14:00"],
      "calendar_rules": {
        "hourly": {
          "enabled": false
        }
      }
    }
  }
}
```
→ **매일 09:30과 14:00에 실행**

### config_advanced.json - 실행 횟수 제한
```json
{
  "run_limit": {
    "max_runs_per_day": 24
  }
}
```
→ **하루에 최대 24번 실행**

## 사용 패턴

### 패턴 1: 실행 시간 확인
```python
scheduler = PortfolioScheduler(config)

# 매분 확인
while True:
    if scheduler.is_execution_time():
        # 리밸런싱 실행
        result = rebalancing_engine.create_rebalance_plan(...)
        executor.execute_plan(result)
        
        # 실행 기록
        scheduler.record_execution()
    
    time.sleep(60)  # 60초마다 확인
```

### 패턴 2: 다음 실행 시간 예측
```python
next_execution = scheduler.get_next_execution_time()
wait_seconds = (next_execution - datetime.now()).total_seconds()
print(f"다음 실행까지 {wait_seconds:.0f}초")
```

### 패턴 3: 일일 횟수 관리
```python
# 오전 실행
if scheduler.is_execution_time():
    # ... 실행
    scheduler.record_execution()

# 저녁 실행  
if scheduler.is_execution_time():
    if scheduler.runs_today >= scheduler.max_runs_per_day:
        print("일일 실행 횟수 초과")
    else:
        # ... 실행
        scheduler.record_execution()
```

## 스케줄 규칙 상세

### Hourly 규칙
```
매시간 minute 분에 실행
예: minute = 0 → 매시간 정각
예: minute = 30 → 매시간 30분
```

### Run Times 규칙
```
지정된 시각들에 정확히 실행
형식: "HH:MM" (24시간 형식)
예: ["09:30", "14:00", "16:00"]
```

### Calendar Rules

#### 월말 (month_end)
```
다음달 1일 이전인 경우 (즉, 오늘이 마지막 날)
예: 1월 31일 → 월말 조건 만족
```

#### 분기말 (quarter_end)
```
3월, 6월, 9월, 12월의 마지막 날
예: 3월 31일 → 분기말이면서 월말
```

#### 주간 (weekly)
```
특정 요일에만 실행
요일: MON(0), TUE(1), WED(2), THU(3), FRI(4), SAT(5), SUN(6)
예: weekday = "FRI" → 매주 금요일
```

## 스케줄 우선순위 흐름

```
is_execution_time() 호출
  ↓
1. 일일 실행 횟수 제한 확인
   - max_runs_per_day 초과? → False 반환
  ↓
2. Hourly 규칙 확인?
   - enabled = true? → 매시간의 minute 분인가? → True/False 반환
  ↓
3. Run Times + Calendar Rules 확인 (Hourly disabled인 경우만)
   - run_times에 현재 HH:MM 포함? → True 반환
   - calendar_rules 조건 만족? (month_end, quarter_end, weekly) → True 반환
  ↓
False 반환
```

## 타임존 처리

```python
# 설정에서 타임존 읽기
timezone_str = config.get_basic("rebalance/schedule/timezone")
# "Asia/Seoul", "US/Eastern", "Europe/London" 등 지원

# 자동으로 ZoneInfo로 변환
scheduler = PortfolioScheduler(config)
# scheduler.timezone = ZoneInfo("Asia/Seoul")

# 현재 시간은 해당 타임존으로 해석
current_time = datetime.now(scheduler.timezone)
```

## 일일 횟수 세기

```python
scheduler = PortfolioScheduler(config)

# 첫 실행
scheduler.record_execution()
print(scheduler.runs_today)  # 1

# 두 번째 실행
scheduler.record_execution()
print(scheduler.runs_today)  # 2

# 다음날 자동 리셋
# (is_execution_time() 호출 시 日付 변경 감지)
```

## 로깅

Logger: `modules.scheduler`

```python
import logging

logger = logging.getLogger("modules.scheduler")
logger.setLevel(logging.DEBUG)

# 스케줄 판단 과정 추적 가능
# "Hourly execution time: 10:00"
# "Calendar rule match: 2025-02-28"
# "Daily run limit reached: 24/24"
```

## 주의사항

1. **타임존**: KIS API는 한국 시간(Asia/Seoul)을 기준으로 동작
2. **경계 시간**: 분 단위 정확도 (초 이하는 무시)
3. **만료 확인**: 토큰 발급은 ZoneInfo 시간으로 계산됨
4. **연속 호출**: 1초 내에 여러 번 is_execution_time() 호출 시 같은 결과 반환 (의도적)

## 성능

- `is_execution_time()`: O(1)
- `get_next_execution_time()`: O(n) (n = run_times 개수)
- 메모리: 무시할 수 있는 수준
