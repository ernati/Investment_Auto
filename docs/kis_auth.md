# kis_auth.py 모듈 문서

## 개요
한국투자증권 Open Trading API의 인증을 처리하는 모듈입니다. 토큰 발급, 관리 및 재사용 기능을 제공합니다.

## 주요 기능
- OAuth 2.0 기반 토큰 발급
- 토큰 파일 저장/로드
- 토큰 만료 시간 자동 체크
- 실전투자/모의투자 환경 지원
- API 호출 헤더 자동 생성

## 클래스

### KISAuth
한국투자증권 API 인증 관리 클래스

#### 생성자
```python
KISAuth(appkey, appsecret, account, product="01", htsid="", env='real')
```

**Parameters:**
- `appkey` (str): API 앱키
- `appsecret` (str): API 앱시크리트
- `account` (str): 계좌번호 (8자리)
- `product` (str): 계좌상품코드 (2자리, 기본값: "01")
  - "01": 주식투자, 위탁계좌, 투자계좌
  - "03": 선물옵션(파생)
  - "08": 해외선물옵션(파생)
  - "22": 개인연금저축계좌
  - "29": 퇴직연금계좌
- `htsid` (str): HTS ID
- `env` (str): 환경 ('real' 또는 'demo')

**도메인 설정:**
- 실전투자(`real`): `https://openapi.koreainvestment.com:9443`
- 모의투자(`demo`): `https://openapivts.koreainvestment.com:29443`

**예제:**
```python
from kis_auth import KISAuth

# 모의투자 인증 객체 생성
auth = KISAuth(
    appkey="YOUR_APP_KEY",
    appsecret="YOUR_APP_SECRET",
    account="12345678",
    product="01",
    htsid="your_hts_id",
    env='demo'
)
```

#### 속성
- `appkey` (str): API 앱키
- `appsecret` (str): API 앱시크리트
- `account` (str): 계좌번호
- `product` (str): 계좌상품코드
- `htsid` (str): HTS ID
- `env` (str): 환경 ('real' 또는 'demo')
- `base_url` (str): API 기본 URL
- `token` (str): 액세스 토큰
- `token_expired` (str): 토큰 만료 시간
- `last_auth_time` (datetime): 마지막 인증 시간
- `token_dir` (Path): 토큰 저장 디렉토리
- `token_file` (Path): 토큰 파일 경로

#### 메서드

##### authenticate()
API 인증을 수행하고 토큰을 발급받습니다.

**Returns:**
- `str`: 액세스 토큰

**동작 방식:**
1. 저장된 토큰 확인
2. 유효한 토큰이 있으면 재사용
3. 없거나 만료되었으면 새 토큰 발급
4. 발급된 토큰을 파일에 저장

**Raises:**
- `Exception`: 인증 실패 시

**예제:**
```python
auth = KISAuth(appkey="...", appsecret="...", account="...", env='demo')
token = auth.authenticate()
print(f"토큰 발급 완료: {token[:20]}...")
```

##### get_headers(tr_id, tr_cont="")
API 호출에 필요한 헤더를 생성합니다.

**Parameters:**
- `tr_id` (str): 거래ID (Transaction ID)
- `tr_cont` (str): 연속조회 여부 ("" 또는 "N": 초기 조회, "M" 또는 "F": 연속 조회)

**Returns:**
- `dict`: API 호출 헤더

**자동 처리:**
- 토큰이 없으면 자동으로 인증 수행
- 모의투자인 경우 TR ID 자동 변환 (예: "T" → "V")

**예제:**
```python
auth = KISAuth(appkey="...", appsecret="...", account="...", env='demo')
auth.authenticate()

# 헤더 생성
headers = auth.get_headers("FHKST01010100")
```

**생성되는 헤더:**
```python
{
    "Content-Type": "application/json",
    "Accept": "text/plain",
    "charset": "UTF-8",
    "authorization": "Bearer {token}",
    "appkey": "{appkey}",
    "appsecret": "{appsecret}",
    "tr_id": "{tr_id}",
    "custtype": "P",
    "tr_cont": "{tr_cont}"
}
```

##### get_env_info()
환경 정보를 반환합니다.

**Returns:**
- `namedtuple`: 환경 정보
  - `appkey`: API 앱키
  - `appsecret`: API 앱시크리트
  - `account`: 계좌번호
  - `product`: 계좌상품코드
  - `htsid`: HTS ID
  - `token`: 액세스 토큰
  - `base_url`: API 기본 URL
  - `env`: 환경 ('real' 또는 'demo')

**예제:**
```python
auth = KISAuth(appkey="...", appsecret="...", account="...", env='demo')
auth.authenticate()

env_info = auth.get_env_info()
print(f"환경: {env_info.env}")
print(f"계좌: {env_info.account}")
```

## 토큰 관리

### 토큰 저장 위치
- 디렉토리: `{사용자홈}/KIS/config/`
- 파일명: `KIS_{env}_{YYYYMMDD}` (예: `KIS_demo_20250207`)

### 토큰 파일 형식
```
token: eyJ0eXAiOiJKV1QiLCJhbGc...
valid-date: 2025-02-08 14:30:00
```

### 토큰 유효기간
- 1일 (24시간)
- 6시간 이내 재발급 시 기존 토큰 재사용
- 발급 시 알림톡 발송

## 사용 예제

### 기본 사용
```python
from kis_auth import KISAuth

# 1. 인증 객체 생성
auth = KISAuth(
    appkey="YOUR_APP_KEY",
    appsecret="YOUR_APP_SECRET",
    account="12345678",
    env='demo'
)

# 2. 인증 수행
token = auth.authenticate()

# 3. API 호출 헤더 생성
headers = auth.get_headers("FHKST01010100")

# 4. 환경 정보 확인
env_info = auth.get_env_info()
print(f"토큰: {env_info.token}")
print(f"기본 URL: {env_info.base_url}")
```

### config_loader와 함께 사용
```python
from config_loader import get_config
from kis_auth import KISAuth

# 설정 로드
config = get_config()
kis_config = config.get_kis_config('demo')

# 인증 객체 생성
auth = KISAuth(
    appkey=kis_config['appkey'],
    appsecret=kis_config['appsecret'],
    account=kis_config['account'],
    product=kis_config['product'],
    htsid=kis_config.get('htsid', ''),
    env='demo'
)

# 인증
auth.authenticate()
```

### 실전투자 환경
```python
from kis_auth import KISAuth

# 실전투자 인증
auth = KISAuth(
    appkey="REAL_APP_KEY",
    appsecret="REAL_APP_SECRET",
    account="12345678",
    env='real'  # 실전투자
)

token = auth.authenticate()
```

## 거래 ID (TR ID) 변환

모의투자 환경에서는 TR ID가 자동으로 변환됩니다:

| 실전투자 | 모의투자 |
|---------|---------|
| TXXXXX  | VXXXXX  |
| JXXXXX  | VXXXXX  |
| CXXXXX  | VXXXXX  |

**예제:**
```python
# 실전투자
auth_real = KISAuth(..., env='real')
headers = auth_real.get_headers("TTTC0802U")  # TR ID: TTTC0802U

# 모의투자
auth_demo = KISAuth(..., env='demo')
headers = auth_demo.get_headers("TTTC0802U")  # TR ID: VTTC0802U (자동 변환)
```

## 에러 처리

```python
from kis_auth import KISAuth

try:
    auth = KISAuth(
        appkey="INVALID_KEY",
        appsecret="INVALID_SECRET",
        account="12345678",
        env='demo'
    )
    token = auth.authenticate()
except Exception as e:
    print(f"인증 실패: {e}")
```

## 주의사항

1. **보안**: 앱키, 앱시크리트는 절대 코드에 하드코딩하지 마세요. 설정 파일이나 환경 변수를 사용하세요.
2. **토큰 관리**: 토큰은 자동으로 저장/로드되므로 직접 관리할 필요가 없습니다.
3. **환경 구분**: 실전투자와 모의투자 환경을 명확히 구분하여 사용하세요.
4. **알림톡**: 실전투자에서 토큰 발급 시 알림톡이 발송됩니다.

## 의존성
- `requests`: HTTP 요청
- `datetime`: 시간 관리
- `pathlib.Path`: 파일 경로 관리
- `collections.namedtuple`: 환경 정보 구조체
- `json`: JSON 처리
