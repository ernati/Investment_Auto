# kis_api_client.py 모듈 문서

## 개요
한국투자증권 Open Trading API를 쉽게 사용할 수 있도록 래핑한 클라이언트 모듈입니다. 주식 시세 조회 등의 기능을 제공합니다.

## 주요 기능
- 주식 현재가 조회
- 시장가 정보 조회
- API 호출 공통 처리
- 에러 처리 및 예외 관리

## 클래스

### KISAPIClient
한국투자증권 API 클라이언트 클래스

#### 클래스 속성
- `STOCK_NAMES` (dict): 주요 종목코드와 종목명 매핑
  - 지원 종목: 삼성전자, SK하이닉스, NAVER, 카카오, LG에너지솔루션, 삼성바이오로직스, 삼성SDI, 현대차, 기아, POSCO홀딩스

#### 생성자
```python
KISAPIClient(auth)
```

**Parameters:**
- `auth`: KISAuth 인증 객체

**예제:**
```python
from kis_auth import KISAuth
from kis_api_client import KISAPIClient

# 인증 객체 생성
auth = KISAuth(
    appkey="YOUR_APP_KEY",
    appsecret="YOUR_APP_SECRET",
    account="12345678",
    env='demo'
)
auth.authenticate()

# API 클라이언트 생성
client = KISAPIClient(auth)
```

#### 메서드

##### inquire_price(stock_code, market_code="J")
주식 현재가를 조회합니다.

**Parameters:**
- `stock_code` (str): 종목코드 (6자리, 예: "005930")
- `market_code` (str): 시장구분코드
  - "J": KRX (거래소 + 코스닥)
  - "NX": NXT (코넥스)
  - "UN": 통합

**Returns:**
- `pd.DataFrame`: 현재가 정보 (전체 필드)

**Raises:**
- `Exception`: API 호출 실패 또는 오류 응답 시

**API 엔드포인트:**
- `/uapi/domestic-stock/v1/quotations/inquire-price`

**TR ID:**
- `FHKST01010100`

**예제:**
```python
client = KISAPIClient(auth)

# 삼성전자 현재가 조회
df = client.inquire_price("005930")
print(df)

# SK하이닉스 현재가 조회
df = client.inquire_price("000660", market_code="J")
print(df)
```

**반환 데이터 (주요 필드):**
```python
{
    'prdt_name': '삼성전자',         # 종목명
    'stck_prpr': '71000',           # 현재가
    'prdy_vrss': '1000',            # 전일대비
    'prdy_ctrt': '1.43',            # 전일대비율
    'stck_oprc': '70500',           # 시가
    'stck_hgpr': '71500',           # 고가
    'stck_lwpr': '70000',           # 저가
    'acml_vol': '12345678',         # 누적거래량
    'acml_tr_pbmn': '87654321000',  # 누적거래대금
    # ... 기타 필드
}
```

##### get_market_price(stock_code, market_code="J")
시장가 정보를 조회합니다. (현재가 조회의 별칭, 주요 정보만 추출)

**Parameters:**
- `stock_code` (str): 종목코드
- `market_code` (str): 시장구분코드

**Returns:**
- `dict`: 주요 시장가 정보

**예제:**
```python
client = KISAPIClient(auth)

# 삼성전자 시장가 조회
market_info = client.get_market_price("005930")
print(market_info)
```

**반환 데이터 구조:**
```python
{
    '종목코드': '005930',
    '종목명': '삼성전자',  # STOCK_NAMES 매핑에서 조회, 없으면 업종명 사용
    '현재가': '71000',
    '전일대비': '1000',
    '등락률': '1.43',
    '시가': '70500',
    '고가': '71500',
    '저가': '70000',
    '거래량': '12345678',
    '거래대금': '87654321000'
}
```

**종목명 조회 방식:**
1. `STOCK_NAMES` 매핑에 종목코드가 있으면 해당 종목명 사용
2. 없으면 API 응답의 `bstp_kor_isnm` (업종명) 사용
3. 추가 종목을 지원하려면 `STOCK_NAMES`에 추가

##### _call_api(endpoint, tr_id, params=None, method='GET', tr_cont="")
API를 호출하는 내부 메서드입니다. (직접 호출 권장하지 않음)

**Parameters:**
- `endpoint` (str): API 엔드포인트
- `tr_id` (str): 거래ID
- `params` (dict): 요청 파라미터
- `method` (str): HTTP 메서드 ('GET' 또는 'POST')
- `tr_cont` (str): 연속조회 여부

**Returns:**
- `dict`: API 응답 (JSON)

**Raises:**
- `Exception`: API 호출 실패 시

## 사용 예제

### 기본 사용
```python
from config_loader import get_config
from kis_auth import KISAuth
from kis_api_client import KISAPIClient

# 1. 설정 로드
config = get_config()
kis_config = config.get_kis_config('demo')

# 2. 인증
auth = KISAuth(
    appkey=kis_config['appkey'],
    appsecret=kis_config['appsecret'],
    account=kis_config['account'],
    env='demo'
)
auth.authenticate()

# 3. API 클라이언트 생성
client = KISAPIClient(auth)

# 4. 현재가 조회
df = client.inquire_price("005930")
print(df)
```

### 여러 종목 조회
```python
from kis_api_client import KISAPIClient

# 종목 리스트
stocks = ["005930", "000660", "035420", "035720"]  # 삼성전자, SK하이닉스, NAVER, 카카오

# 각 종목의 시장가 조회
for stock_code in stocks:
    market_info = client.get_market_price(stock_code)
    print(f"{market_info['종목명']}: {int(market_info['현재가']):,}원")
```

### 상세 정보 조회
```python
# 전체 데이터 조회
df = client.inquire_price("005930")

# 특정 필드 접근
current_price = df.iloc[0]['stck_prpr']
stock_name = df.iloc[0]['prdt_name']
volume = df.iloc[0]['acml_vol']

print(f"{stock_name}: {current_price}원, 거래량: {volume}주")
```

### 간편한 시장가 조회
```python
# 주요 정보만 추출
market_info = client.get_market_price("005930")

# 출력
print(f"종목: {market_info['종목명']}")
print(f"현재가: {int(market_info['현재가']):,}원")
print(f"전일대비: {market_info['전일대비']}원 ({market_info['등락률']}%)")
print(f"거래량: {int(market_info['거래량']):,}주")
```

### 에러 처리
```python
from kis_api_client import KISAPIClient

try:
    client = KISAPIClient(auth)
    df = client.inquire_price("005930")
    
    if not df.empty:
        print("조회 성공")
    else:
        print("데이터가 비어있습니다")
        
except Exception as e:
    print(f"API 호출 오류: {e}")
```

## API 응답 구조

### 성공 응답
```json
{
    "rt_cd": "0",
    "msg_cd": "SUCCESS",
    "msg1": "정상처리 되었습니다.",
    "output": {
        "prdt_name": "삼성전자",
        "stck_prpr": "71000",
        "prdy_vrss": "1000",
        // ... 기타 필드
    }
}
```

### 오류 응답
```json
{
    "rt_cd": "1",
    "msg_cd": "EGW00123",
    "msg1": "조회 오류 메시지"
}
```

## 주요 종목코드

| 종목명 | 종목코드 |
|-------|---------|
| 삼성전자 | 005930 |
| SK하이닉스 | 000660 |
| NAVER | 035420 |
| 카카오 | 035720 |
| LG에너지솔루션 | 373220 |
| 삼성바이오로직스 | 207940 |
| 삼성SDI | 006400 |
| 현대차 | 005380 |
| 기아 | 000270 |
| POSCO홀딩스 | 005490 |

※ 종목코드는 6자리 숫자입니다.

## 시장 구분 코드

| 코드 | 설명 |
|-----|------|
| J | KRX (거래소 + 코스닥) |
| NX | NXT (코넥스) |
| UN | 통합 |

## 반환 필드 설명

### inquire_price() 주요 필드

| 필드명 | 설명 | 예시 |
|-------|------|------|
| prdt_name | 종목명 | "삼성전자" |
| stck_prpr | 현재가 | "71000" |
| prdy_vrss | 전일대비 | "1000" |
| prdy_ctrt | 전일대비율 | "1.43" |
| stck_oprc | 시가 | "70500" |
| stck_hgpr | 고가 | "71500" |
| stck_lwpr | 저가 | "70000" |
| acml_vol | 누적거래량 | "12345678" |
| acml_tr_pbmn | 누적거래대금 | "87654321000" |
| stck_mxpr | 상한가 | "91500" |
| stck_llam | 하한가 | "50500" |
| per | PER | "12.34" |
| pbr | PBR | "1.23" |
| eps | EPS | "5678" |
| bps | BPS | "45678" |

※ 모든 수치는 문자열로 반환됩니다.

## 주의사항

1. **시세 데이터**: REST API는 실시간 데이터가 아닙니다. 실시간 시세는 WebSocket API를 사용하세요.
2. **API 호출 제한**: 초당 호출 횟수에 제한이 있을 수 있습니다.
3. **장 운영 시간**: 장 운영 시간 외에는 전일 종가 데이터가 조회됩니다.
4. **ETN 종목**: ETN 종목은 종목코드 앞에 'Q'를 붙여야 합니다 (예: "Q123456")
5. **데이터 형식**: 반환되는 수치 데이터는 모두 문자열이므로 필요시 형변환하세요.

## 장 운영 시간

| 구분 | 시간 |
|-----|------|
| 정규장 | 09:00 ~ 15:30 |
| 시간외 종가 | 15:40 ~ 16:00 |
| 시간외 단일가 | 16:00 ~ 18:00 |

## 의존성
- `requests`: HTTP 요청
- `pandas`: 데이터프레임 처리
- `typing`: 타입 힌트

## 추가 기능 (향후 확장 가능)

현재는 시세 조회만 구현되어 있지만, 다음 기능들을 추가할 수 있습니다:

- 호가 조회
- 일자별 시세 조회
- 차트 데이터 조회
- 체결 데이터 조회
- 투자자별 매매 동향
- 거래량 순위
- 주식 주문 (매수/매도)
- 계좌 잔고 조회
- 주문 내역 조회

이러한 기능들은 `KISAPIClient` 클래스에 메서드를 추가하여 구현할 수 있습니다.
