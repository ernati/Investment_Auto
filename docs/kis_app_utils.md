# kis_app_utils.py 모듈 문서

## 개요
KIS API 애플리케이션 개발을 위한 공통 유틸리티 모듈입니다. 반복적인 초기화 로직, 출력 포맷팅, 에러 처리 등을 제공합니다.

## 주요 기능
- KIS API 클라이언트 자동 설정
- 일관된 출력 포맷팅
- 공통 에러 처리
- 진행 상황 출력 헬퍼

## 함수

### setup_kis_client(env='real')
KIS API 클라이언트를 설정하고 반환합니다.

**동작:**
1. 설정 파일 로드
2. KIS API 인증
3. API 클라이언트 생성

**Parameters:**
- `env` (str): 환경 ('real' 또는 'demo', 기본값: 'real')

**Returns:**
- `tuple`: (KISAPIClient, dict) - API 클라이언트와 설정 정보

**Raises:**
- `FileNotFoundError`: 설정 파일을 찾을 수 없을 때
- `ValueError`: KIS 설정이 잘못되었을 때
- `Exception`: 인증 실패 시

**예제:**
```python
from kis_app_utils import setup_kis_client

# 실전 클라이언트 설정 (기본값)
client, config = setup_kis_client()

# 모의투자 클라이언트 설정
client, config = setup_kis_client('demo')

# 시장가 조회
market_info = client.get_market_price("005930")
print(f"현재가: {market_info['현재가']}원")
```

### setup_kis_trading_client(env='real')
KIS API 거래 클라이언트를 설정하고 반환합니다.

**동작:**
1. 설정 파일 로드
2. KIS API 인증
3. API 클라이언트 및 거래 클라이언트 생성

**Parameters:**
- `env` (str): 환경 ('real' 또는 'demo', 기본값: 'real')

**Returns:**
- `tuple`: (KISAPIClient, KISTrading, dict) - API 클라이언트, 거래 클라이언트, 설정 정보

**Raises:**
- `FileNotFoundError`: 설정 파일을 찾을 수 없을 때
- `ValueError`: KIS 설정이 잘못되었을 때
- `Exception`: 인증 실패 시

**예제:**
```python
from kis_app_utils import setup_kis_trading_client

# 실전 거래 클라이언트 설정 (기본값)
api_client, trading, config = setup_kis_trading_client()

# 모의투자 거래 클라이언트 설정
api_client, trading, config = setup_kis_trading_client('demo')

# 현재가 조회
market_info = api_client.get_market_price("005930")

# 매수 주문
buy_result = trading.buy_market_order("005930", 1)
if buy_result['success']:
    print(f"매수 성공! 주문번호: {buy_result['order_no']}")
```

### print_info(message, prefix="[INFO]")
타임스탬프가 포함된 정보 메시지를 출력합니다.

**Parameters:**
- `message` (str): 출력할 메시지
- `prefix` (str): 메시지 접두어 (기본값: "[INFO]")

**예제:**
```python
from kis_app_utils import print_info

print_info("프로그램 시작")
# 출력: [INFO] 2026-02-08 00:00:00 - 프로그램 시작

print_info("매수 완료", prefix="[SUCCESS]")
# 출력: [SUCCESS] 2026-02-08 00:00:01 - 매수 완료

print_info("오류 발생", prefix="[ERROR]")
# 출력: [ERROR] 2026-02-08 00:00:02 - 오류 발생
```

### print_header(title, width=60)
헤더를 출력합니다.

**Parameters:**
- `title` (str): 제목
- `width` (int): 출력 너비 (기본값: 60)

**예제:**
```python
from kis_app_utils import print_header

print_header("삼성전자 시장가 조회")
# 출력:
# ============================================================
# 삼성전자 시장가 조회
# ============================================================
```

### print_separator(width=60, char="-")
구분선을 출력합니다.

**Parameters:**
- `width` (int): 구분선 너비 (기본값: 60)
- `char` (str): 구분선 문자 (기본값: "-")

**예제:**
```python
from kis_app_utils import print_separator

print_separator()
# 출력: ------------------------------------------------------------

print_separator(40, "=")
# 출력: ========================================
```

### format_number(value, unit="")
숫자를 포맷팅합니다.

**Parameters:**
- `value`: 숫자 값 (문자열 또는 숫자)
- `unit` (str): 단위 (예: "원", "주")

**Returns:**
- `str`: 포맷팅된 문자열

**예제:**
```python
from kis_app_utils import format_number

print(format_number("71000", "원"))
# 출력: 71,000원

print(format_number(1234567, "주"))
# 출력: 1,234,567주
```

### print_market_info(market_info, show_details=True)
시장가 정보를 포맷팅하여 출력합니다.

**Parameters:**
- `market_info` (dict): 시장가 정보
- `show_details` (bool): 상세 정보 표시 여부 (기본값: True)

**예제:**
```python
from kis_app_utils import setup_kis_client, print_market_info

client, _ = setup_kis_client('demo')
market_info = client.get_market_price("005930")

# 상세 정보 포함 출력
print_market_info(market_info, show_details=True)

# 간단한 정보만 출력
print_market_info(market_info, show_details=False)
```

**출력 예시:**
```
============================================================
조회 결과
============================================================

종목코드: 005930
종목명: 삼성전자
------------------------------------------------------------
현재가: 71,000원
전일대비: 1000원 (1.43%)
------------------------------------------------------------
시가: 70,500원
고가: 71,500원
저가: 70,000원
------------------------------------------------------------
거래량: 12,345,678주
거래대금: 876,543,210,000원
============================================================
```

### handle_common_errors(func)
공통 에러 처리 데코레이터입니다.

**Parameters:**
- `func`: 래핑할 함수

**Returns:**
- `function`: 래핑된 함수

**처리하는 예외:**
- `FileNotFoundError`: 설정 파일 없음
- `ValueError`: 잘못된 설정 값
- `Exception`: 기타 모든 예외

**예제:**
```python
from kis_app_utils import handle_common_errors

@handle_common_errors
def main():
    # 설정 파일이 없거나 API 호출 실패 시
    # 자동으로 에러 메시지 출력
    client, _ = setup_kis_client('demo')
    market_info = client.get_market_price("005930")
    print(market_info)

if __name__ == "__main__":
    main()
```

## 클래스

### ProgressPrinter
진행 상황 출력 헬퍼 클래스입니다.

#### 생성자
```python
ProgressPrinter(title="처리 진행")
```

**Parameters:**
- `title` (str): 진행 상황 제목 (기본값: "처리 진행")

#### 메서드

##### print_step(message)
단계별 진행 상황을 출력합니다.

**Parameters:**
- `message` (str): 출력할 메시지

**예제:**
```python
from kis_app_utils import ProgressPrinter

progress = ProgressPrinter()

progress.print_step("설정 파일 로드 중...")
# 출력: [1] 설정 파일 로드 중...

progress.print_step("API 인증 중...")
# 출력: [2] API 인증 중...
```

##### print_sub_step(message)
하위 단계 정보를 출력합니다.

**Parameters:**
- `message` (str): 출력할 메시지

**예제:**
```python
progress = ProgressPrinter()

progress.print_step("설정 로드 중...")
progress.print_sub_step("환경: demo")
progress.print_sub_step("계좌: 12345678")

# 출력:
# [1] 설정 로드 중...
#    - 환경: demo
#    - 계좌: 12345678
```

## 사용 예제

### 기본 사용 패턴

```python
from kis_app_utils import (
    setup_kis_client,
    print_header,
    print_market_info,
    handle_common_errors,
    ProgressPrinter
)

@handle_common_errors
def main():
    # 진행 상황 출력
    progress = ProgressPrinter()
    
    # 타이틀
    print_header("주식 조회 프로그램")
    
    # 클라이언트 설정
    progress.print_step("설정 및 인증 중...")
    client, config = setup_kis_client('demo')
    progress.print_sub_step(f"계좌: {config['account']}")
    
    # 데이터 조회
    progress.print_step("시장가 조회 중...")
    market_info = client.get_market_price("005930")
    
    # 결과 출력
    print()
    print_market_info(market_info)

if __name__ == "__main__":
    main()
```

### 여러 종목 조회

```python
from kis_app_utils import setup_kis_client, print_market_info, ProgressPrinter

def main():
    progress = ProgressPrinter()
    
    # 설정
    progress.print_step("클라이언트 설정 중...")
    client, _ = setup_kis_client('demo')
    
    # 종목 리스트
    stocks = ["005930", "000660", "035420"]
    
    # 각 종목 조회
    progress.print_step("종목 조회 중...")
    for stock_code in stocks:
        market_info = client.get_market_price(stock_code)
        print()
        print_market_info(market_info, show_details=False)

if __name__ == "__main__":
    main()
```

### 커스텀 출력

```python
from kis_app_utils import (
    setup_kis_client,
    print_header,
    print_separator,
    format_number
)

def main():
    client, _ = setup_kis_client('demo')
    market_info = client.get_market_price("005930")
    
    print_header("커스텀 출력")
    print(f"\n종목: {market_info['종목명']} ({market_info['종목코드']})")
    print_separator()
    print(f"현재가: {format_number(market_info['현재가'], '원')}")
    print(f"거래량: {format_number(market_info['거래량'], '주')}")
    print_separator()

if __name__ == "__main__":
    main()
```

## 모듈 의존성

이 모듈은 다음 모듈들을 사용합니다:
- `config_loader`: 설정 파일 로드
- `kis_auth`: KIS API 인증
- `kis_api_client`: KIS API 클라이언트

## 장점

### 1. 코드 중복 제거
- 초기화 로직을 한 곳에서 관리
- 반복적인 출력 코드 제거

### 2. 일관성
- 모든 앱에서 동일한 출력 포맷 사용
- 통일된 에러 처리

### 3. 생산성 향상
- 새로운 앱 작성 시 빠른 개발
- 보일러플레이트 코드 최소화

### 4. 유지보수성
- 공통 로직 수정이 모든 앱에 자동 반영
- 버그 수정이 용이

## 새 앱 작성 템플릿

```python
# -*- coding: utf-8 -*-
"""
새 애플리케이션 설명
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent / "modules"))

from kis_app_utils import (
    setup_kis_client,
    print_header,
    print_market_info,
    handle_common_errors,
    ProgressPrinter
)

@handle_common_errors
def main():
    progress = ProgressPrinter()
    
    # 1. 타이틀
    print_header("앱 제목")
    
    # 2. 클라이언트 설정
    progress.print_step("설정 및 인증 중...")
    client, config = setup_kis_client('demo')
    progress.print_sub_step("인증 완료")
    
    # 3. 로직 작성
    progress.print_step("작업 수행 중...")
    # 여기에 앱 로직 작성
    
    # 4. 결과 출력
    print()
    # 결과 출력 코드

if __name__ == "__main__":
    main()
```

## 참고 사항

1. **환경 선택**: 항상 모의투자(`'demo'`)로 먼저 테스트하세요
2. **에러 처리**: `@handle_common_errors` 데코레이터 사용 권장
3. **출력 일관성**: `print_market_info()` 등 제공된 함수 사용
4. **진행 표시**: 사용자 친화적인 출력을 위해 `ProgressPrinter` 활용

## 관련 문서
- [config_loader.md](config_loader.md)
- [kis_auth.md](kis_auth.md)
- [kis_api_client.md](kis_api_client.md)
- [samsung_price_inquiry.md](samsung_price_inquiry.md)
