# kis_bond_trading.py 모듈 문서

## 개요
`kis_bond_trading.py`는 한국투자증권 Open Trading API를 사용하여 장내채권 매매(매수/매도) 기능을 제공하는 모듈입니다.
실전투자와 모의투자를 자동으로 구분하여 적절한 TR ID를 사용합니다.

## 파일 위치
- **경로**: `Investment_Auto/Scripts/modules/kis_bond_trading.py`
- **유형**: 모듈 (Module)

## 주요 기능

### 1. 실전투자/모의투자 자동 구분
- KISAuth 객체의 `env` 설정에 따라 자동으로 TR ID를 선택합니다
- **실전투자 (env="real")**: T로 시작하는 TR ID 사용
  - 매수: TTTC0952U
  - 매도: TTTC0958U
- **모의투자 (env="demo")**: V로 시작하는 TR ID 사용
  - 매수: VTTC0952U
  - 매도: VTTC0958U

### 2. KISBondTrading 클래스
한국투자증권 API를 통해 장내채권 매매를 수행하는 클래스입니다.

#### 초기화
```python
from kis_bond_trading import KISBondTrading
from kis_auth import KISAuth

# 실전투자 인증 객체 생성
auth_real = KISAuth(appkey, appsecret, account, product, htsid, env='real')
auth_real.authenticate()

# 모의투자 인증 객체 생성  
auth_demo = KISAuth(appkey, appsecret, account, product, htsid, env='demo')
auth_demo.authenticate()

# 채권 거래 객체 생성
bond_trading_real = KISBondTrading(auth_real)  # 실전투자
bond_trading_demo = KISBondTrading(auth_demo)  # 모의투자
```

#### 주요 메서드

##### order_bond()
장내채권 주문을 실행하는 기본 메서드입니다.

**파라미터:**
- `bond_code` (str): 채권코드 (예: "KR6095572D81" - 삼성전자 관련채권)
- `order_type` (str): 주문유형 ("buy" 또는 "sell")
- `quantity` (int): 주문수량
- `price` (str): 채권주문단가
- `samt_mket_ptci_yn` (str, optional): 동시시장참여여부 (기본값: "N")
- `bond_rtl_mket_yn` (str, optional): 채권소매시장여부 (기본값: "Y")

**반환값:**
```python
{
    'success': True/False,      # 성공 여부
    'order_no': '주문번호',      # 주문번호 (성공시)
    'order_time': '주문시각',    # 주문시각 (성공시)
    'message': '결과메시지',     # 결과 메시지
    'data': {}                  # 원본 API 응답 데이터
}
```

**예제:**
```python
# 채권 매수
result = bond_trading.order_bond(
    bond_code="KR6095572D81",
    order_type="buy",
    quantity=1,
    price="10000"
)

if result['success']:
    print(f"매수 성공! 주문번호: {result['order_no']}")
else:
    print(f"매수 실패: {result['message']}")
```

##### buy_bond()
채권 매수 주문을 실행합니다.

**파라미터:**
- `bond_code` (str): 채권코드
- `quantity` (int): 주문수량
- `price` (str): 채권주문단가

**예제:**
```python
result = bond_trading.buy_bond("KR6095572D81", 1, "10000")
```

##### sell_bond()
채권 매도 주문을 실행합니다.

**파라미터:**
- `bond_code` (str): 채권코드
- `quantity` (int): 주문수량  
- `price` (str): 채권주문단가

**예제:**
```python
result = bond_trading.sell_bond("KR6095572D81", 1, "10000")
```

##### get_bond_info()
채권 기본 정보를 조회합니다.

**파라미터:**
- `bond_code` (str): 채권코드
- `prdt_type_cd` (str, optional): 상품유형코드 (기본값: "302")

**예제:**
```python
info = bond_trading.get_bond_info("KR6095572D81")
if info['success']:
    print(f"채권 정보: {info['data']}")
```

## 의존성 모듈
- `kis_auth`: 한국투자증권 API 인증 모듈
- `requests`: HTTP 요청 라이브러리
- `pandas`: 데이터 처리 라이브러리

## 사용 예제

### 1. 실전투자 모드 채권 거래
```python
import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent.parent / "modules"))

from config_loader import get_config
from kis_auth import KISAuth
from kis_bond_trading import KISBondTrading

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

# 3. 채권 거래 객체 생성
bond_trading = KISBondTrading(auth)

# 4. 채권 매수 주문 실행 (실전투자 TR ID: TTTC0952U 사용)
result = bond_trading.buy_bond("KR6095572D81", 1, "10000")
print(f"채권 매수 결과: {result}")
```

### 2. 모의투자 모드 채권 거래
```python
import sys
from pathlib import Path

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent.parent / "modules"))

from config_loader import get_config
from kis_auth import KISAuth
from kis_bond_trading import KISBondTrading

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

# 3. 채권 거래 객체 생성
bond_trading = KISBondTrading(auth)

# 4. 채권 매수 주문 실행 (모의투자 TR ID: VTTC0952U 사용)
result = bond_trading.buy_bond("KR6095572D81", 1, "10000")
print(f"채권 매수 결과: {result}")
```

## TR ID 정보

### 장내채권 거래 TR ID
| 구분 | 실전투자 | 모의투자 | API 엔드포인트 |
|------|----------|----------|---------------|
| 매수 | TTTC0952U | VTTC0952U | /uapi/domestic-bond/v1/trading/buy |
| 매도 | TTTC0958U | VTTC0958U | /uapi/domestic-bond/v1/trading/sell |
| 정보조회 | CTPF1114R | CTPF1114R | /uapi/domestic-bond/v1/quotations/search-bond-info |

### TR ID 자동 선택 로직
```python
# kis_bond_trading.py 내부 로직
if self.auth.env == "real":
    # 실전투자용 TR ID
    if order_type == "buy":
        tr_id = "TTTC0952U"  # 실전투자 채권 매수 
    else:  # sell
        tr_id = "TTTC0958U"  # 실전투자 채권 매도
else:  # demo
    # 모의투자용 TR ID
    if order_type == "buy":
        tr_id = "VTTC0952U"  # 모의투자 채권 매수
    else:  # sell
        tr_id = "VTTC0958U"  # 모의투자 채권 매도
```

## 채권 코드 예시

### 삼성전자 관련 채권
- **코드**: KR6095572D81
- **설명**: 삼성전자 관련채권
- **사용**: config_basic.json에 포트폴리오 구성종목으로 추가됨

### 기타 채권 예시
- KR103502GA34: 기타 우량채권
- KR2033022D33: 또 다른 채권 예시

*주의: 실제 거래 전 채권 정보와 상태를 반드시 확인하시기 바랍니다.*

## API 엔드포인트
- **매수 URL**: `/uapi/domestic-bond/v1/trading/buy`
- **매도 URL**: `/uapi/domestic-bond/v1/trading/sell`  
- **정보조회 URL**: `/uapi/domestic-bond/v1/quotations/search-bond-info`
- **Method**: POST
- **인증**: Bearer Token 필요

## 관련 문서
- [한국투자증권 Open Trading API 문서](https://apiportal.koreainvestment.com/)
- [kis_auth.py 모듈 문서](kis_auth.md)
- [kis_trading.py 모듈 문서](kis_trading.md)
- [bond_trading_demo.py 앱 문서](bond_trading_demo.md)

## 버전 정보
- **작성일**: 2026-02-16
- **작성자**: GitHub Copilot
- **버전**: 1.0.0