# kis_overseas_trading.py 모듈 문서

## 개요
`kis_overseas_trading.py`는 한국투자증권 Open Trading API를 사용하여 해외주식 매매(매수/매도) 기능을 제공하는 모듈입니다.
미국, 홍콩, 중국, 일본, 베트남 등 다양한 해외 거래소의 주식 거래를 지원하며, 실전투자와 모의투자를 자동으로 구분합니다.

## 파일 위치
- **경로**: `Investment_Auto/Scripts/modules/kis_overseas_trading.py`
- **유형**: 모듈 (Module)

## 주요 특징 (v1.0.0)

### 🌍 다양한 해외 거래소 지원
- **미국**: NASD(나스닥), NYSE(뉴욕), AMEX(아멕스)
- **홍콩**: SEHK
- **중국**: SHAA(상해), SZAA(심천)
- **일본**: TKSE
- **베트남**: HASE(하노이), VNSE(호치민)

### 🎯 Real/Demo 자동 구분
- `env="real"`: 실전투자 TR ID 사용 (T로 시작)
- `env="demo"`: 모의투자 TR ID 사용 (V로 시작)
- `build_api_headers`에서 자동 변환 처리

### 📊 주요 기능
- 해외주식 주문 (매수/매도)
- 미국 주간거래 주문
- 주문 정정/취소
- 현재가 조회
- 잔고 조회

## 사용 방법

### 1. 초기화
```python
from modules.kis_auth import KISAuth
from modules.kis_overseas_trading import KISOverseasTrading

# 인증 객체 생성
kis_auth = KISAuth(
    appkey="YOUR_APP_KEY",
    appsecret="YOUR_APP_SECRET",
    account="YOUR_ACCOUNT",
    product="01",
    htsid="YOUR_HTS_ID",
    env='demo'  # 또는 'real'
)
kis_auth.authenticate()

# 해외주식 거래 객체 생성
overseas_trading = KISOverseasTrading(kis_auth)
```

### 2. 현재가 조회
```python
# AAPL(애플) 현재가 조회
result = overseas_trading.get_current_price("AAPL", "NASD")

if result['success']:
    print(f"현재가: ${result['current_price']}")
    print(f"전일대비: {result['change']:+.2f} ({result['change_rate']:+.2f}%)")
```

### 3. 잔고 조회
```python
# 미국 주식 잔고 조회
result = overseas_trading.get_balance(exchange_code="NASD", currency="USD")

if result['success']:
    print(f"보유 종목 수: {len(result['holdings'])}")
    for holding in result['holdings']:
        print(f"  {holding['symbol']}: {holding['quantity']}주")
```

### 4. 지정가 주문
```python
# 애플 1주 $150에 매수
buy_result = overseas_trading.buy_limit_order(
    stock_code="AAPL",
    exchange_code="NASD",
    quantity=1,
    price=150.00
)

# 테슬라 2주 $200에 매도
sell_result = overseas_trading.sell_limit_order(
    stock_code="TSLA",
    exchange_code="NASD",
    quantity=2,
    price=200.00
)
```

### 5. 시장가 주문 (미국 주식)
```python
# 모의투자에서는 현재가 조회 후 지정가로 자동 변환
buy_result = overseas_trading.buy_market_order_us("AAPL", "NASD", 1)
sell_result = overseas_trading.sell_market_order_us("TSLA", "NASD", 2)
```

### 6. 미국 주간거래
```python
# 미국 주간거래 시간에만 가능 (한국 기준 23:30~06:00)
result = overseas_trading.daytime_order(
    stock_code="AAPL",
    exchange_code="NASD",
    order_type="buy",
    quantity=1,
    price="150.00",
    order_division="00"  # 지정가만 가능
)
```

### 7. 주문 취소/정정
```python
# 주문 취소
cancel_result = overseas_trading.cancel_order(
    stock_code="AAPL",
    exchange_code="NASD",
    original_order_no="123456789"
)

# 주문 정정
modify_result = overseas_trading.modify_order(
    stock_code="AAPL",
    exchange_code="NASD",
    original_order_no="123456789",
    quantity=2,
    price=155.00
)
```

## API 상세

### KISOverseasTrading 클래스

#### 생성자
```python
def __init__(self, auth: KISAuth)
```
- `auth`: KISAuth 인증 객체

#### 메서드

##### order()
해외주식 주문 실행

```python
def order(
    stock_code: str,      # 종목코드 (예: "AAPL")
    exchange_code: str,   # 거래소코드 (예: "NASD")
    order_type: str,      # "buy" 또는 "sell"
    quantity: int,        # 주문수량
    price: str = "0",     # 주문단가
    order_division: str = "00"  # 주문구분
) -> Dict[str, Any]
```

**주문구분 코드 (미국 매수):**
- `"00"`: 지정가
- `"32"`: LOO (장개시지정가)
- `"34"`: LOC (장마감지정가)

**주문구분 코드 (미국 매도):**
- `"00"`: 지정가
- `"31"`: MOO (장개시시장가)
- `"32"`: LOO (장개시지정가)
- `"33"`: MOC (장마감시장가)
- `"34"`: LOC (장마감지정가)

**주문구분 코드 (홍콩 매도):**
- `"00"`: 지정가
- `"50"`: 단주지정가

**⚠️ 모의투자 제한:** 모의투자에서는 `"00"` 지정가만 가능

##### daytime_order()
미국 주간거래 주문

```python
def daytime_order(
    stock_code: str,
    exchange_code: str,   # "NASD", "NYSE", "AMEX"만 가능
    order_type: str,
    quantity: int,
    price: str,           # 지정가 필수
    order_division: str = "00"
) -> Dict[str, Any]
```

##### modify_cancel_order()
주문 정정/취소

```python
def modify_cancel_order(
    stock_code: str,
    exchange_code: str,
    original_order_no: str,
    action: str,          # "modify" 또는 "cancel"
    quantity: int = 0,    # 정정 시 필수
    price: str = "0"      # 정정 시 필수, 취소 시 "0"
) -> Dict[str, Any]
```

##### get_current_price()
현재가 조회

```python
def get_current_price(
    stock_code: str,
    exchange_code: str
) -> Dict[str, Any]
```

**반환값:**
```python
{
    'success': True,
    'symbol': 'AAPL',
    'exchange': 'NASD',
    'current_price': 150.25,
    'change': 2.30,
    'change_rate': 1.55,
    'message': '현재가 조회 성공',
    'data': {...}  # 원본 API 응답
}
```

##### get_balance()
잔고 조회

```python
def get_balance(
    exchange_code: str = "NASD",
    currency: str = "USD"
) -> Dict[str, Any]
```

**통화 코드:**
- `"USD"`: 미국 달러
- `"HKD"`: 홍콩 달러
- `"CNY"`: 중국 위안화
- `"JPY"`: 일본 엔화
- `"VND"`: 베트남 동

**반환값:**
```python
{
    'success': True,
    'holdings': [
        {
            'symbol': 'AAPL',
            'name': 'APPLE INC',
            'quantity': 10,
            'avg_price': 145.50,
            'current_price': 150.25,
            'profit_loss': 47.50,
            'profit_rate': 3.26,
            'exchange': 'NASD'
        },
        ...
    ],
    'summary': {
        'total_evaluation': 1502.50,
        'total_profit_rate': 3.26,
        ...
    },
    'message': '잔고 조회 성공',
    'data': {...}
}
```

## TR ID 매핑

### 매수 주문
| 거래소 | 실전 TR ID | 모의 TR ID |
|--------|-----------|-----------|
| 미국 (NASD/NYSE/AMEX) | TTTT1002U | VTTT1002U |
| 홍콩 (SEHK) | TTTS1002U | VTTS1002U |
| 중국상해 (SHAA) | TTTS0202U | VTTS0202U |
| 중국심천 (SZAA) | TTTS0305U | VTTS0305U |
| 일본 (TKSE) | TTTS0308U | VTTS0308U |
| 베트남 (HASE/VNSE) | TTTS0311U | VTTS0311U |

### 매도 주문
| 거래소 | 실전 TR ID | 모의 TR ID |
|--------|-----------|-----------|
| 미국 (NASD/NYSE/AMEX) | TTTT1006U | VTTT1006U |
| 홍콩 (SEHK) | TTTS1001U | VTTS1001U |
| 중국상해 (SHAA) | TTTS1005U | VTTS1005U |
| 중국심천 (SZAA) | TTTS0304U | VTTS0304U |
| 일본 (TKSE) | TTTS0307U | VTTS0307U |
| 베트남 (HASE/VNSE) | TTTS0310U | VTTS0310U |

### 기타
| 기능 | 실전 TR ID | 모의 TR ID |
|------|-----------|-----------|
| 정정/취소 | TTTT1004U | VTTT1004U |
| 잔고조회 | TTTS3012R | VTTS3012R |
| 현재가조회 | HHDFS00000300 | HHDFS00000300 |
| 미국 주간 매수 | TTTS6036U | - |
| 미국 주간 매도 | TTTS6037U | - |

## 에러 처리

### 주요 에러 코드
- **EGW00123**: 토큰 만료 → 자동 갱신 후 재시도
- **EGW00201**: Rate limit 초과 → 백오프 후 재시도
- **APBK0919**: 매매 가능 시간외 → 시간 확인 필요
- **APBK0930**: 잔고 부족 → 잔고 확인 필요

### 에러 응답 예시
```python
{
    'success': False,
    'order_no': '',
    'message': '[APBK0930] 주문가능금액을 초과한 주문',
    'data': {...}
}
```

## 테스트

테스트 실행 방법:
```bash
cd Investment_Auto/Scripts/tests
python kis_debug.py --overseas
```

## 의존성

- `kis_auth.py`: API 인증 처리
- `kis_api_utils.py`: API 공통 유틸리티

## 참고 문서

- [한국투자증권 Open API 포털](https://apiportal.koreainvestment.com)
- [해외주식 API 가이드](https://apiportal.koreainvestment.com/apiservice/overseas-stock)
- [에러 코드 안내](https://apiportal.koreainvestment.com/faq-error-code)

## 변경 이력

### v1.0.0 (2026-03-22)
- 최초 버전
- 해외주식 주문 (매수/매도) 기능
- 미국 주간거래 주문 기능
- 주문 정정/취소 기능
- 현재가 조회 기능
- 잔고 조회 기능
- demo/real 모드 자동 구분 지원
