# kis_trading.py 모듈 문서

## 개요
`kis_trading.py`는 한국투자증권 Open Trading API를 사용하여 주식 매매(매수/매도) 기능을 제공하는 모듈입니다.
실전투자와 모의투자를 자동으로 구분하여 적절한 TR ID를 사용하며, 모의투자 환경에서는 안전한 가상 현금 관리 기능이 통합되어 있습니다.

## 파일 위치
- **경로**: `Investment_Auto/Scripts/modules/kis_trading.py`
- **유형**: 모듈 (Module)

## 주요 특징 (v2.1.0)

### 🏛️ 안전한 체결가 관리 시스템
- **실제 체결가 우선**: API 응답에서 실제 체결 정보 추출
- **현재가 API 백업**: 체결가 미확인 시 실시간 현재가 조회  
- **확인 불가 시 보류**: 모든 방법 실패 시 현금 업데이트 중단
- **예상가 사용 금지**: 부정확한 추정가 사용 완전 제거

### 🎯 모의투자 현금 관리
- **자동 현금 업데이트**: 주문 성공 시 자동으로 가상 현금 차감/증가
- **정확한 금액 반영**: 실제/현재가 기반 정확한 계산
- **안전 장치**: 현금 부족 시 매수 차단

## 주요 기능

### 1. 실전투자/모의투자 자동 구분
- KISAuth 객체의 `env` 설정에 따라 자동으로 TR ID를 선택합니다
- **실전투자 (env="real")**: T로 시작하는 TR ID 사용 (예: TTTC0012U)
- **모의투자 (env="demo")**: V로 시작하는 TR ID 사용 (예: VTTC0012U)

### 2. KISTrading 클래스
한국투자증권 API를 통해 주식 매매를 수행하는 클래스입니다.

#### 초기화
```python
from kis_trading import KISTrading
from kis_auth import KISAuth

# 실전투자 인증 객체 생성
auth_real = KISAuth(appkey, appsecret, account, product, htsid, env='real')
auth_real.authenticate()

# 모의투자 인증 객체 생성  
auth_demo = KISAuth(appkey, appsecret, account, product, htsid, env='demo')
auth_demo.authenticate()

# 거래 객체 생성
trading_real = KISTrading(auth_real)  # 실전투자
trading_demo = KISTrading(auth_demo)  # 모의투자
```

#### 주요 메서드

##### order_cash()
현금 주식 주문을 실행하는 기본 메서드입니다.

**파라미터:**
- `stock_code` (str): 종목코드 (예: "005930" - 삼성전자)
- `order_type` (str): 주문유형 ("buy" 또는 "sell")
- `quantity` (int): 주문수량
- `price` (str, optional): 주문단가 (기본값: "0" - 시장가)
- `order_division` (str, optional): 주문구분 (기본값: "01" - 시장가)
- `excg_id_dvsn_cd` (str, optional): 거래소ID구분코드 (기본값: "SOR")

**주문구분 코드:**
- `"00"`: 지정가
- `"01"`: 시장가
- `"02"`: 조건부지정가
- `"03"`: 최유리지정가
- `"04"`: 최우선지정가
- `"05"`: 장전시간외
- `"06"`: 장후시간외
- `"07"`: 시간외단일가
- `"11"`: IOC지정가
- `"12"`: FOK지정가

**거래소ID구분코드:**
- `"SOR"`: Smart Order Routing (기본값)
- `"KRX"`: 한국거래소
- `"NXT"`: NASDAQ
- `"13"`: IOC시장가
- `"14"`: FOK시장가
- `"15"`: IOC최유리
- `"16"`: FOK최유리

**반환값:**
```python
{
    'success': True/False,      # 성공 여부
    'order_no': '주문번호',      # 주문번호
    'order_time': '주문시각',    # 주문시각
    'message': '결과 메시지',    # 결과 메시지
    'data': {...}               # 원본 응답 데이터
}
```

**예제:**
```python
# 시장가 주문
result = trading.order_cash(
    stock_code="005930",
    order_type="buy",
    quantity=1,
    price="0",
    order_division="01"
)

# 지정가 주문
result = trading.order_cash(
    stock_code="005930",
    order_type="buy",
    quantity=10,
    price="70000",
    order_division="00"
)
```

##### buy_market_order()
시장가 매수 주문을 간편하게 실행합니다.

**파라미터:**
- `stock_code` (str): 종목코드
- `quantity` (int): 주문수량

**예제:**
```python
result = trading.buy_market_order("005930", 1)
if result['success']:
    print(f"매수 주문 성공! 주문번호: {result['order_no']}")
else:
    print(f"매수 주문 실패: {result['message']}")
```

##### sell_market_order()
시장가 매도 주문을 간편하게 실행합니다.

**파라미터:**
- `stock_code` (str): 종목코드
- `quantity` (int): 주문수량

**예제:**
```python
result = trading.sell_market_order("005930", 1)
if result['success']:
    print(f"매도 주문 성공! 주문번호: {result['order_no']}")
else:
    print(f"매도 주문 실패: {result['message']}")
```

##### buy_limit_order()
지정가 매수 주문을 실행합니다.

**파라미터:**
- `stock_code` (str): 종목코드
- `quantity` (int): 주문수량
- `price` (int): 주문단가

**예제:**
```python
result = trading.buy_limit_order("005930", 10, 70000)
```

##### sell_limit_order()
지정가 매도 주문을 실행합니다.

**파라미터:**
- `stock_code` (str): 종목코드
- `quantity` (int): 주문수량
- `price` (int): 주문단가

**예제:**
```python
result = trading.sell_limit_order("005930", 10, 75000)
```

## 의존성 모듈
- `kis_auth`: 한국투자증권 API 인증 모듈
- `requests`: HTTP 요청 라이브러리
- `pandas`: 데이터 처리 라이브러리

## 사용 예제

### 1. 실전투자 모드 사용 예제
```python
import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent.parent / "modules"))

from config_loader import get_config
from kis_auth import KISAuth
from kis_trading import KISTrading

# 1. 설정 로드 (실전투자)
config = get_config()
kis_config = config.get_kis_config('real')

# 2. 실전투자 인증
auth = KISAuth(
    appkey=kis_config['appkey'],
    appsecret=kis_config['appsecret'],
    account=kis_config['account'],
    product=kis_config['product'],
    htsid=kis_config.get('htsid', ''),
    env='real'  # 실전투자
)
auth.authenticate()

# 3. 거래 객체 생성
trading = KISTrading(auth)

# 4. 매수 주문 실행 (실전투자 TR ID: TTTC0012U 사용)
result = trading.buy_market_order("005930", 1)
print(f"매수 주문 결과: {result}")
```

### 2. 모의투자 모드 사용 예제
```python
import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent.parent / "modules"))

from config_loader import get_config
from kis_auth import KISAuth
from kis_trading import KISTrading

# 1. 설정 로드 (모의투자)
config = get_config()
kis_config = config.get_kis_config('demo')

# 2. 모의투자 인증
auth = KISAuth(
    appkey=kis_config['appkey'],
    appsecret=kis_config['appsecret'],
    account=kis_config['account'],
    product=kis_config['product'],
    htsid=kis_config.get('htsid', ''),
    env='demo'  # 모의투자
)
auth.authenticate()

# 3. 거래 객체 생성
trading = KISTrading(auth)

# 4. 매수 주문 실행 (모의투자 TR ID: VTTC0012U 사용)
result = trading.buy_market_order("005930", 1)
print(f"매수 주문 결과: {result}")
```

### 3. 명령줄 옵션을 사용한 앱 예제
```python
import argparse
from kis_app_utils import setup_kis_trading_client

def main():
    # 명령줄 인수 파싱
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="모의투자 모드")
    args = parser.parse_args()
    
    # 환경 설정
    env = "demo" if args.demo else "real"
    
    # 클라이언트 설정
    api_client, trading, kis_config = setup_kis_trading_client(env)
    
    # 거래 실행
    result = trading.buy_market_order("005930", 1)
    print(f"주문 결과: {result}")

if __name__ == "__main__":
    main()
```

**실행 방법:**
```bash
# 실전투자 모드
python my_trading_app.py

# 모의투자 모드  
python my_trading_app.py --demo
```

### 4. TR ID 확인 예제
```python
# 환경별 TR ID 확인
if auth.env == "real":
    print("실전투자 TR ID:")
    print("  - 매수: TTTC0012U")
    print("  - 매도: TTTC0011U")
else:
    print("모의투자 TR ID:")
    print("  - 매수: VTTC0012U")  
    print("  - 매도: VTTC0011U")
```

## TR ID 신버전 정보

### 현금 주문 TR ID (신버전)
| 구분 | 실전투자 | 모의투자 | 설명 |
|------|----------|----------|------|
| 매수 | TTTC0012U | VTTC0012U | 현금 매수 주문 |
| 매도 | TTTC0011U | VTTC0011U | 현금 매도 주문 |

### TR ID 자동 선택 로직
```python
# kis_trading.py 내부 로직
if self.auth.env == "real":
    # 실전투자용 TR ID (신버전)
    if order_type == "buy":
        tr_id = "TTTC0012U"  # 실전투자 매수 
    else:  # sell
        tr_id = "TTTC0011U"  # 실전투자 매도
else:  # demo
    # 모의투자용 TR ID (신버전)
    if order_type == "buy":
        tr_id = "VTTC0012U"  # 모의투자 매수
    else:  # sell
        tr_id = "VTTC0011U"  # 모의투자 매도
buy_result = trading.buy_market_order("005930", 1)
print(f"매수 결과: {buy_result}")

# 5. 매도 주문 실행
sell_result = trading.sell_market_order("005930", 1)
print(f"매도 결과: {sell_result}")
```

## 주의사항

1. **환경 구분**
   - `demo` 환경: 모의투자 (실제 거래 없음)
   - `real` 환경: 실전투자 (실제 거래 발생)
   - 테스트 시 반드시 `demo` 환경을 사용하세요.

2. **TR ID 자동 변환**
   - `KISAuth` 객체가 환경에 따라 TR ID를 자동으로 변환합니다.
   - 실전투자: `TTTC0801U` (매도), `TTTC0802U` (매수)
   - 모의투자: `VTTC0801U` (매도), `VTTC0802U` (매수)

3. **시장가 주문**
   - `price="0"`이고 `order_division="01"`일 때 시장가로 주문됩니다.
   - 시장가 주문은 즉시 체결되지만 체결가격이 예상과 다를 수 있습니다.

4. **오류 처리**
   - 모든 메서드는 예외를 발생시키지 않고 결과 딕셔너리를 반환합니다.
   - `success` 필드를 확인하여 주문 성공 여부를 판단하세요.
   - 실패 시 `message` 필드에 오류 메시지가 포함됩니다.

5. **주문 제한**
   - 계좌 잔고, 거래 한도 등을 고려해야 합니다.
   - 주문 전 `inquire_psbl_order` API로 주문 가능 수량을 확인하는 것이 좋습니다.

## API 엔드포인트
- **URL**: `/uapi/domestic-stock/v1/trading/order-cash`

---

## ⚠️ 중요 업데이트 (v2.1.0 - 2026.02.24)

### 🏛️ 안전한 체결가 확인 시스템 도입

기존 **예상 체결가 사용 방식의 문제점**을 해결하고, **일반적인 거래 시스템 표준**에 맞춘 안전한 체결가 확인 시스템을 도입했습니다.

### ❌ 이전 방식의 문제점
```python
# v2.0.0 - 부정확한 예상 체결가 사용
estimated_prices = {
    "005930": 75000.0,   # 고정된 추정가 (실제와 다를 수 있음)
    "000660": 130000.0,  # 시세 변동 미반영
}
executed_price = estimated_prices.get(stock_code, 50000.0)  # 부정확!!
```

**문제점:**
- 실제 체결가와 달라 현금 잔액 부정확
- 시세 변동 미반영으로 모의투자 경험 왜곡
- 일반적인 거래 시스템과 다른 방식

### ✅ 현재 방식의 개선 사항
```python
# v2.1.0 - 안전한 체결가 확인 시스템
def _get_execution_price(self, api_output, stock_code, price, order_division):
    # 1. 지정가 주문: 입력된 가격 사용
    if price != "0" and order_division == "00":
        return float(price)  # 정확한 지정가
    
    # 2. API 응답에서 실제 체결가 추출 시도
    executed_price = self._extract_executed_price_from_response(api_output)
    if executed_price is not None:
        return executed_price  # 실제 체결가
    
    # 3. 현재가 API로 실시간 가격 조회
    current_price = self._get_current_market_price(stock_code)
    if current_price is not None:
        return current_price  # 실시간 현재가
    
    # 4. 모든 방법 실패 시 현금 업데이트 안함
    return None  # 안전한 처리
```

### 📊 체결가 확인 순서

| 순서 | 방법 | 설명 | 정확성 |
|------|------|------|--------|
| 1 | **지정가 주문** | 입력된 가격 사용 | ⭐⭐⭐ 최고 |
| 2 | **API 응답** | 실제 체결가 추출 | ⭐⭐⭐ 최고 |
| 3 | **현재가 API** | 실시간 시세 조회 | ⭐⭐ 높음 |
| 4 | **확인 불가** | 현금 업데이트 보류 | ⭐⭐⭐ 안전 |

### 🔍 API 응답 체결가 추출

**확인하는 필드들:**
```python
price_fields = [
    'avg_prvs',      # 평균단가
    'tot_ccld_amt',  # 총체결금액  
    'ccld_unpr',     # 체결단가
    'avg_unpr',      # 평균단가
    'ord_unpr'       # 주문단가
]
```

### 📱 현재가 API 백업 조회

**kis_api_client 활용:**
```python
from .kis_api_client import KISAPIClient

api_client = KISAPIClient(self.auth)
market_info = api_client.get_market_price(stock_code)

if market_info and '현재가' in market_info:
    current_price = float(market_info['현재가'].replace(',', ''))
    return current_price  # 실시간 현재가 사용
```

### 🛡️ 체결가 확인 불가 시 안전 처리

**일반적인 거래 시스템과 동일한 방식:**
```python
if executed_price is None:
    # 체결가를 전혀 확인할 수 없는 경우
    logger.warning(f"Demo 체결가 확인 불가 - 현금 업데이트 보류: {stock_code}")
    logger.info("체결 확인 후 수동으로 현금 업데이트를 진행하세요.")
    # ✅ 주문은 성공하지만 현금 업데이트는 보류 (안전)
else:
    # ✅ 체결가 확인된 경우만 정확한 금액으로 현금 업데이트
    demo_manager.buy_stock(stock_code, quantity, executed_price)
```

### 📝 향상된 로깅 시스템

**정상 동작 로그:**
```
INFO - 지정가 주문 체결가: 75,000원
INFO - Demo 매수 현금 차감: 005930 10주 x 75,000원 = 750,000원

INFO - API 응답에서 체결가 확인: 74,800원  
INFO - Demo 매수 현금 차감: 005930 10주 x 74,800원 = 748,000원

INFO - 현재가 API로 체결가 확인: 74,900원
```

**체결가 확인 실패 로그:**
```
WARNING - Demo 체결가 확인 불가 - 현금 업데이트 보류: 005930
INFO - 체결 확인 후 수동으로 현금 업데이트를 진행하세요.
```

### 🎯 사용자 경험 개선

**이전:**
- 부정확한 예상가로 현금 차감/증가
- 실제 거래와 다른 경험
- 시세 변동 미반영

**현재:**
- 실제 체결가/현재가 기반 정확한 현금 관리
- 실제 거래 시스템과 동일한 경험
- 체결가 확인 불가 시 안전한 보류 처리

### 💡 사용 권장사항

1. **지정가 주문 우선 사용**
   ```python
   # 정확한 가격으로 거래
   result = trading.buy_limit_order("005930", 10, 75000)
   ```

2. **시장가 주문 시 로그 확인**
   ```python
   # 실제 체결가 확인
   result = trading.buy_market_order("005930", 10)
   # 로그에서 "체결가 확인: XX원" 메시지 확인
   ```

3. **체결가 미확인 시 수동 처리**
   ```python
   # 주문 성공하지만 현금 업데이트 보류된 경우
   from modules.demo_cash_manager import get_demo_cash_manager
   
   manager = get_demo_cash_manager(account)
   manager.buy_stock("005930", 10, 74500)  # 수동으로 실제 체결가 입력
   ```

이제 **일반적인 거래 시스템과 동일한 방식**으로 안전하고 정확한 현금 관리를 제공합니다! 🚀
- **Method**: POST
- **인증**: Bearer Token 필요

## 관련 문서
- [한국투자증권 Open Trading API 문서](https://apiportal.koreainvestment.com/)
- [kis_auth.py 모듈 문서](kis_auth.md)
- [config_loader.py 모듈 문서](config_loader.md)

## 버전 정보
- **작성일**: 2026-02-07
- **작성자**: GitHub Copilot
- **버전**: 1.0.0
