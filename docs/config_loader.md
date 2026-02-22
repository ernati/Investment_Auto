# config_loader.py 모듈 문서

## 개요
JSON 형식의 설정 파일을 로드하고 관리하는 모듈입니다.

## 주요 기능
- JSON 설정 파일 로드
- 중첩된 키 경로로 설정 값 조회
- KIS API 설정 관리
- 전역 설정 로더 인스턴스 제공

## 클래스

### ConfigLoader
설정 파일을 로드하고 관리하는 클래스

#### 생성자
```python
ConfigLoader(config_path=None)
```
- `config_path` (str, optional): 설정 파일 경로. None이면 기본 경로 사용
  - 기본 경로: `{프로젝트_루트}/Config/config.json`

#### 메서드

##### load()
설정 파일을 로드합니다.

**Returns:**
- `dict`: 설정 데이터

**Raises:**
- `FileNotFoundError`: 설정 파일이 없을 경우
- `json.JSONDecodeError`: JSON 파싱 오류 시

**예제:**
```python
loader = ConfigLoader()
config = loader.load()
```

##### get(key_path, default=None)
중첩된 키 경로로 설정 값을 가져옵니다.

**Parameters:**
- `key_path` (str): 점(.)으로 구분된 키 경로 (예: "kis.real.appkey")
- `default`: 키가 없을 때 반환할 기본값

**Returns:**
- 설정 값 또는 기본값

**예제:**
```python
loader = ConfigLoader()
appkey = loader.get("kis.real.appkey")
appkey_with_default = loader.get("kis.real.appkey", "default_value")
```

##### get_kis_config(env='real')
KIS API 설정을 가져옵니다.

**Parameters:**
- `env` (str): 환경 ('real' 또는 'demo')

**Returns:**
- `dict`: KIS API 설정 (appkey, appsecret, account, product, htsid)

**Raises:**
- `ValueError`: 해당 환경의 설정을 찾을 수 없을 때

**예제:**
```python
loader = ConfigLoader()
real_config = loader.get_kis_config('real')
demo_config = loader.get_kis_config('demo')
```

## 전역 함수

### get_config(reload=False)
전역 설정 로더 인스턴스를 가져옵니다.

**Parameters:**
- `reload` (bool): 설정을 다시 로드할지 여부

**Returns:**
- `ConfigLoader`: 설정 로더 인스턴스

**예제:**
```python
from config_loader import get_config

# 전역 설정 로더 가져오기
config = get_config()

# 설정 값 조회
appkey = config.get("kis.real.appkey")

# 설정 리로드
config = get_config(reload=True)
```

## 설정 파일 형식

설정 파일(`Config/config.json`)은 다음과 같은 형식이어야 합니다:

```json
{
    "kis": {
        "real": {
            "appkey": "실전투자_앱키",
            "appsecret": "실전투자_앱시크리트",
            "account": "계좌번호_8자리",
            "product": "01",
            "htsid": "HTS_ID"
        },
        "demo": {
            "appkey": "모의투자_앱키",
            "appsecret": "모의투자_앱시크리트",
            "account": "모의투자_계좌번호",
            "product": "01",
            "htsid": "HTS_ID"
        }
    }
}
```

**파일 위치:** `Investment_Auto/Config/config.json`
- ConfigLoader는 `Scripts/modules/config_loader.py`에서 자동으로 프로젝트 루트의 `Config` 폴더를 찾습니다.

## 사용 예제

### 기본 사용
```python
from config_loader import get_config

# 설정 로드
config = get_config()

# KIS 실전투자 설정 가져오기
real_config = config.get_kis_config('real')
print(f"App Key: {real_config['appkey']}")
print(f"Account: {real_config['account']}")
```

### 커스텀 경로 사용
```python
from config_loader import ConfigLoader

# 커스텀 경로로 설정 로더 생성
loader = ConfigLoader("/path/to/custom/config.json")
config = loader.load()
```

### 중첩 키 조회
```python
from config_loader import get_config

config = get_config()

# 중첩된 키로 값 조회
appkey = config.get("kis.real.appkey")
account = config.get("kis.demo.account")

# 기본값 지정
custom_value = config.get("custom.key.path", "default_value")
```

## 주의사항

1. **보안**: 설정 파일에는 민감한 정보(API 키, 계좌번호 등)가 포함되므로 버전 관리 시스템에 커밋하지 마세요.
2. **파일 위치**: 기본적으로 프로젝트 루트의 `Config/config.json`을 사용합니다.
3. **에러 처리**: 설정 파일이 없거나 잘못된 형식일 경우 적절한 예외가 발생합니다.

## 의존성
- Python 표준 라이브러리만 사용 (외부 의존성 없음)
  - `json`
  - `os`
  - `pathlib.Path`
