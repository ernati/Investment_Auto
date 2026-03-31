# Market Hours Module (market_hours.py)

## Overview
한국 주식 시장(KRX) 및 해외 주식 시장(NYSE, NASDAQ, AMEX 등) 기준 장 상태를 계산하는 유틸리티입니다.
리밸런싱 실행 전에 장 열림 여부를 확인하여 불필요한 API 호출 및 오류를 줄입니다.

## 주요 기능

### 1. 한국 시장 장 상태 계산
- 평일 기준 장 시작/종료 시간은 09:00~15:30 (KST)
- 주말은 `closed_weekend`로 판단
- 장 시작 전/후를 구분하여 상태를 제공합니다

### 2. 해외 시장 장 상태 계산 (2026-04-01 추가)
지원하는 해외 거래소:
| 거래소 코드 | 시장 | 시간대 | 장 시간 |
|------------|------|--------|---------|
| NYSE | 뉴욕 증권거래소 | America/New_York | 09:30~16:00 |
| NASD | 나스닥 | America/New_York | 09:30~16:00 |
| AMEX | 아멕스 | America/New_York | 09:30~16:00 |
| SEHK | 홍콩 | Asia/Hong_Kong | 09:30~16:00 |
| SHAA | 상해 | Asia/Shanghai | 09:30~15:00 |
| SZAA | 심천 | Asia/Shanghai | 09:30~15:00 |
| TKSE | 도쿄 | Asia/Tokyo | 09:00~15:00 |

### 3. 상태 객체
`MarketStatus`는 다음 정보를 포함합니다:
- `status`: `open`, `pre_open`, `after_close`, `closed_weekend`
- `is_open`: 장 열림 여부
- `now`: 기준 시간
- `session_start`, `session_end`: 장 시작/종료 시각
- `next_open`: 다음 장 시작 시각

## 사용 예시

### 한국 시장 상태 확인
```python
from modules.market_hours import get_market_status, format_market_status

status = get_market_status()
print(format_market_status(status))

if not status.is_open:
    print("Market closed, skip trading")
```

### 해외 시장 상태 확인
```python
from modules.market_hours import (
    get_us_market_status, 
    get_overseas_market_status, 
    is_overseas_market_open,
    format_market_status
)

# 미국 시장 상태 확인
us_status = get_us_market_status(exchange_code="AMEX")
print(f"미국 시장: {format_market_status(us_status)}")

# 해외 시장 열림 여부만 확인
if is_overseas_market_open("AMEX"):
    print("미국 시장 열림 - 주문 가능")
else:
    print("미국 시장 휴장 - 주문 스킵")

# 홍콩 시장 상태 확인
hk_status = get_overseas_market_status("SEHK")
print(f"홍콩 시장: {format_market_status(hk_status)}")
```

## API 참조

### `get_market_status(current_time, timezone)`
한국 시장(KRX) 상태를 반환합니다.

### `get_us_market_status(current_time, exchange_code)`
미국 시장(NYSE/NASDAQ/AMEX) 상태를 반환합니다.

### `get_overseas_market_status(exchange_code, current_time)`
지정된 해외 거래소의 장 상태를 반환합니다.

### `is_overseas_market_open(exchange_code, current_time)`
해외 거래소가 현재 열려있는지 확인합니다.
- **Returns**: `bool` - 시장이 열려있으면 `True`

### `format_market_status(status)`
시장 상태를 로그용 문자열로 변환합니다.

## 변경 이력

### 2026-04-01
- 해외 시장 시간 체크 기능 추가
  - `get_us_market_status()`: 미국 시장 상태 조회
  - `get_overseas_market_status()`: 해외 거래소별 상태 조회
  - `is_overseas_market_open()`: 해외 시장 열림 여부 간편 확인
- 지원 거래소: NYSE, NASD, AMEX, SEHK, SHAA, SZAA, TKSE

## 참고
- 공휴일은 별도 로직에 포함되어 있지 않습니다.
- 서머타임(DST)은 시스템 타임존 라이브러리(zoneinfo)가 자동 처리합니다.
- 필요 시 별도의 휴장일 캘린더를 결합하여 확장 가능합니다.
