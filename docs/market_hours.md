# Market Hours Module (market_hours.py)

## Overview
한국 주식 시장(KRX) 기준 장 상태를 계산하는 유틸리티입니다.
리밸런싱 실행 전에 장 열림 여부를 확인하여 불필요한 API 호출 및 오류를 줄입니다.

## 주요 기능

### 1. 장 상태 계산
- 평일 기준 장 시작/종료 시간은 09:00~15:30 (KST)
- 주말은 `closed_weekend`로 판단
- 장 시작 전/후를 구분하여 상태를 제공합니다

### 2. 상태 객체
`MarketStatus`는 다음 정보를 포함합니다:
- `status`: `open`, `pre_open`, `after_close`, `closed_weekend`
- `is_open`: 장 열림 여부
- `now`: 기준 시간
- `session_start`, `session_end`: 장 시작/종료 시각
- `next_open`: 다음 장 시작 시각

## 사용 예시
```python
from modules.market_hours import get_market_status, format_market_status

status = get_market_status()
print(format_market_status(status))

if not status.is_open:
    print("Market closed, skip trading")
```

## 참고
- 공휴일은 별도 로직에 포함되어 있지 않습니다.
- 필요 시 별도의 휴장일 캘린더를 결합하여 확장 가능합니다.
