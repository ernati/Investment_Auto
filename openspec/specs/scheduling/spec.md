# Spec: Scheduling

**Capability:** `scheduling`  
**Source:** `Scripts/modules/scheduler.py`  
**Last synced:** 2026-04-18

---

## Purpose

리밸런싱 실행 시점을 결정한다. "지금 실행해야 하는가?"에만 답한다 — 실행 자체는 하지 않는다. 일일 실행 횟수 카운터를 내부 상태로 관리한다.

---

## Interface

```python
PortfolioScheduler(config_loader: PortfolioConfigLoader)

is_execution_time(current_time: Optional[datetime] = None) -> bool
record_execution(execution_time: Optional[datetime] = None) -> None
get_next_execution_time(current_time: Optional[datetime] = None) -> Optional[datetime]
```

**호출 패턴:**
```python
if scheduler.is_execution_time():
    success = run_rebalancing()
    if success:
        scheduler.record_execution()
```

---

## Decision Logic

```
is_execution_time(now)
  │
  ├─ 날짜 변경됐으면 runs_today = 0 리셋
  │
  ├─ runs_today >= max_runs_per_day → False
  │
  ├─ hourly_enabled = True
  │     → now.minute == hourly_minute ? True : False
  │
  └─ hourly_enabled = False
        ├─ run_times에 now "HH:MM"이 있으면 → True
        └─ calendar rule 매칭?
              ├─ month_end = True AND 오늘이 월말 → True
              ├─ quarter_end = True AND 오늘이 분기말 → True
              └─ weekly_enabled = True AND 오늘 요일 == weekly_weekday → True
```

**우선순위:** hourly > run_times > calendar rules  
hourly가 활성화되면 run_times와 calendar rules는 무시된다.

---

## Schedule Modes

### Hourly 모드
```
config: rebalance/schedule/calendar_rules/hourly/enabled = true
        rebalance/schedule/calendar_rules/hourly/minute = 30

동작: 매시 30분마다 실행 (09:30, 10:30, 11:30, ...)
주의: run_scheduler의 check_interval(기본 60초)보다 자주 체크하면 중복 실행 가능
      → check_interval을 60초로 유지하면 매분 체크하므로 정각 분에만 실행됨
```

### Run Times 모드
```
config: rebalance/schedule/run_times = ["09:00", "15:20"]

동작: 지정 시각에 정확히 실행
주의: check_interval=60초이면 HH:MM이 정확히 매칭되는 분에만 True
      → run_scheduler가 해당 분의 00초에 체크하지 않으면 놓칠 수 있음
```

### Calendar Rules 모드
```
config:
  rebalance/schedule/calendar_rules/month_end = true      # 매월 말일
  rebalance/schedule/calendar_rules/quarter_end = true    # 3/6/9/12월 말일
  rebalance/schedule/calendar_rules/weekly/enabled = true
  rebalance/schedule/calendar_rules/weekly/weekday = "FRI" # MON/TUE/WED/THU/FRI/SAT/SUN

동작: 조건에 해당하는 날에 True (하루 종일 True, max_runs_per_day로 횟수 제한 필요)
```

---

## State Management

```
내부 상태:
  runs_today: int          # 오늘 실행 횟수
  last_run_time: datetime  # 마지막 실행 시각
  last_reset_date: datetime # 마지막 카운터 리셋 날짜

리셋 조건: current_time.date() != last_reset_date.date()
           (날짜가 바뀌면 runs_today = 0)
```

**주의:** 상태는 메모리에만 존재. 프로세스 재시작 시 초기화됨.  
→ 재시작 직후 당일 이미 실행했어도 `runs_today=0`으로 시작.

---

## Configuration Parameters

| 파라미터 | Config 경로 | 기본값 | 소스 |
|---------|------------|--------|------|
| 타임존 | `rebalance/schedule/timezone` | `"Asia/Seoul"` | basic |
| Hourly 활성화 | `rebalance/schedule/calendar_rules/hourly/enabled` | `False` | basic |
| Hourly 분 | `rebalance/schedule/calendar_rules/hourly/minute` | `0` | basic |
| 실행 시각 목록 | `rebalance/schedule/run_times` | `[]` | basic |
| 월말 규칙 | `rebalance/schedule/calendar_rules/month_end` | `False` | basic |
| 분기말 규칙 | `rebalance/schedule/calendar_rules/quarter_end` | `False` | basic |
| 주간 활성화 | `rebalance/schedule/calendar_rules/weekly/enabled` | `False` | basic |
| 주간 요일 | `rebalance/schedule/calendar_rules/weekly/weekday` | `"FRI"` | basic |
| 일일 최대 실행 | `run_limit/max_runs_per_day` | `999` | **advanced** |

---

## Timezone

모든 시간 계산은 `rebalance/schedule/timezone` (기본: `Asia/Seoul` = KST = UTC+9)으로 수행.  
타임존 파싱 실패 시 `Asia/Seoul`로 fallback.

`run_scheduler`의 루프는 `time.sleep(check_interval)`로 동작하므로 DST 전환 시 정확도 영향 받을 수 있음.

---

## Market Hours 연동

`PortfolioScheduler`는 장 시간을 직접 체크하지 않는다.  
장 시간 체크는 `portfolio_rebalancing.py`의 `run_once()`에서 `market_hours` 모듈을 별도로 호출.

```
is_execution_time() → True
  → market_hours.get_market_status() 체크 (run_once 내부)
    → 장 마감이면 return False
```

---

## Invariants

1. `is_execution_time()` 이 `True`를 반환해도 리밸런싱이 실행된다는 보장 없음 — 장 시간, 포트폴리오 조건에 따라 다름
2. `record_execution()`은 리밸런싱 성공 후에만 호출할 것 — 실패 시 호출하면 횟수 소진
3. 상태는 프로세스 생애주기에만 유효
4. `get_next_execution_time()`은 근사값 — calendar rules 모드에서 정확하지 않을 수 있음

---

## Known Issues

- `run_times` 체크는 분(minute) 단위 정확도 — `check_interval=60`일 때 최대 1분 오차
- 프로세스 재시작 시 당일 `runs_today` 리셋 → `max_runs_per_day` 제한이 재시작 전후로 합산되지 않음
- calendar rules 모드에서 `get_next_execution_time()`이 `None` 반환 (run_times 없는 경우)
