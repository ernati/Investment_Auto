# KIS Trading Module 문서

## 개요
한국투자증권 Open Trading API를 통한 주식 거래(매수/매도) 기능을 제공하는 모듈입니다.

## 파일 위치
- **스크립트 파일**: `Scripts/modules/kis_trading.py`
- **의존성 모듈**: `kis_api_utils.py`, `kis_auth.py`, `demo_cash_manager.py`

## 주요 기능

### 1. KISTrading 클래스
한국투자증권 API 거래를 처리하는 메인 클래스입니다.

#### 초기화
```python
kis_trading = KISTrading(auth)
```
- `auth`: KISAuth 인증 객체

### 2. 주문 실행 기능

#### `order_cash()` - 현금 주식 주문
```python
result = kis_trading.order_cash(
    stock_code="005930",     # 종목코드 (삼성전자)
    order_type="buy",        # "buy" 또는 "sell"
    quantity=10,             # 주문수량
    price="0",              # 주문단가 ("0"=시장가)
    order_division="01"      # 주문구분 ("01"=시장가, "00"=지정가)
)
```

**주문구분 코드**:
- `"00"`: 지정가
- `"01"`: 시장가
- `"02"`: 조건부지정가
- `"03"`: 최유리지정가
- `"04"`: 최우선지정가
- `"11"`: IOC지정가
- `"12"`: FOK지정가

**반환값**:
```python
{
    'success': bool,          # 성공 여부
    'order_no': str,          # 주문번호
    'order_time': str,        # 주문시각
    'message': str,           # 결과 메시지
    'data': dict             # 원본 응답 데이터
}
```

#### 편의 메서드들
```python
# 시장가 매수
result = kis_trading.buy_market_order("005930", 10)

# 시장가 매도  
result = kis_trading.sell_market_order("005930", 10)

# 지정가 매수
result = kis_trading.buy_limit_order("005930", 10, 75000)

# 지정가 매도
result = kis_trading.sell_limit_order("005930", 10, 75000)
```

### 3. 내부 유틸리티 기능

#### `_call_api()` - API 공통 호출
- KIS API 요청을 위한 공통 메서드
- 인증 헤더 자동 생성 및 rate limiting 적용

#### `_get_execution_price_with_retry()` - 체결가 조회
- 주문 체결 후 실제 체결가격을 재시도로 조회
- 모의투자 환경에서 현금 잔액 업데이트용

#### `_get_current_market_price()` - 현재가 조회
- 실시간 주식 현재가 정보 조회
- 시장가 주문 시 참고용

## 환경별 TR ID 자동 변환

### 실전투자 환경 (`real`)
- 매수: `TTTC0012U`
- 매도: `TTTC0011U`

### 모의투자 환경 (`demo`)  
- 매수: `VTTC0012U`
- 매도: `VTTC0011U`

## 모의투자 특별 기능

### 가상 현금 관리
- 모의투자 환경에서만 작동하는 현금 잔액 시뮬레이션
- 매수 시 현금 차감, 매도 시 현금 증가
- `demo_cash_manager.py` 모듈과 연동

### 체결가 추적
- 모의투자에서는 실제 체결 정보가 제한적
- 체결가 재시도 조회로 정확한 현금 업데이트 실행

## 에러 처리

### Rate Limiting
- KIS API의 호출 제한을 자동으로 처리
- 실전: 0.1초, 모의: 0.5초 지연 적용

### 재시도 메커니즘  
- 체결 정보 조회: 3회 재시도 (1.5초 간격)
- API 호출 실패: 지수적 백오프 전략

### 로깅
- 모든 주요 동작을 INFO 레벨로 로깅
- 에러 발생 시 ERROR 레벨로 상세 정보 기록

## 사용 예제

### 기본 매수 주문
```python
from modules.kis_auth import KISAuth
from modules.kis_trading import KISTrading

# 인증 초기화
auth = KISAuth()

# 거래 클래스 초기화
trading = KISTrading(auth)

# 삼성전자 10주 시장가 매수
result = trading.buy_market_order("005930", 10)

if result['success']:
    print(f"매수 성공: 주문번호 {result['order_no']}")
else:
    print(f"매수 실패: {result['message']}")
```

### 지정가 매도 주문
```python
# 삼성전자 5주를 75,000원에 지정가 매도  
result = trading.sell_limit_order("005930", 5, 75000)

print(f"주문 결과: {result['message']}")
```

## 설정 파일
- **API 인증 정보**: `Config/config.json`
  ```json
  {
    "APPKEY": "your_app_key",
    "APPSECRET": "your_app_secret"
  }
  ```

## 관련 모듈
- **인증**: `kis_auth.py`
- **API 유틸**: `kis_api_utils.py` 
- **현금 관리**: `demo_cash_manager.py`
- **포트폴리오**: `kis_portfolio_fetcher.py`

## 에러 코드 참고
- KIS API 에러 코드: https://apiportal.koreainvestment.com/faq-error-code

## 최근 수정 사항 (2026-03-03)
- **버그 수정**: 중복된 `_call_api` 메서드 제거
- **API 호출 오류 해결**: `json` → `json_data` 파라미터 수정
- **안정성 향상**: 단일 API 호출 메서드로 통일