# Investment_Auto 프로젝트

한국투자증권 Open Trading API를 사용한 주식 자동매매 및 시세 조회 프로젝트

## 프로젝트 구조

```
Investment_Auto/
├── Config/
│   └── config.json          # API 키 및 계좌 정보 설정
├── Scripts/
│   ├── apps/                # 애플리케이션 스크립트
│   │   └── samsung_price_inquiry.py  # 삼성전자 시장가 조회
│   └── modules/             # 공통 모듈
│       ├── config_loader.py         # 설정 파일 로더
│       ├── kis_auth.py              # KIS API 인증
│       ├── kis_api_client.py        # KIS API 클라이언트
│       └── kis_app_utils.py         # 공통 유틸리티 (NEW)
└── docs/                    # 문서
    ├── README.md
    ├── config_loader.md
    ├── kis_auth.md
    ├── kis_api_client.md
    ├── kis_app_utils.md     # (NEW)
    └── samsung_price_inquiry.md
```

## 시작하기

### 1. 필수 패키지 설치

```bash
pip install requests pandas
```

### 2. 설정 파일 구성

`Config/config.json` 파일을 생성하고 API 키 정보를 입력합니다:

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

### 3. API 키 발급

1. [한국투자증권 API 포털](https://apiportal.koreainvestment.com/)에 접속
2. 회원가입 및 로그인
3. 앱 등록 후 앱키와 앱시크리트 발급
4. 모의투자 및 실전투자 각각 발급 가능

### 4. 첫 실행

```bash
cd Scripts/apps
python samsung_price_inquiry.py
```

## 주요 기능

### 1. 시세 조회
- 주식 현재가 조회
- 전일대비, 등락률
- 시가/고가/저가
- 거래량/거래대금

### 2. 인증 관리
- 자동 토큰 발급
- 토큰 캐싱 및 재사용
- 토큰 만료 자동 체크

### 3. 설정 관리
- JSON 기반 설정
- 실전투자/모의투자 환경 분리
- 안전한 키 관리

## 모듈 설명

### kis_app_utils.py
애플리케이션 개발을 위한 공통 유틸리티 모듈

**주요 기능:**
- 클라이언트 자동 설정
- 출력 포맷팅
- 에러 처리
- 진행 상황 표시

**사용 예제:**
```python
from kis_app_utils import setup_kis_client, print_market_info

# 자동 설정
client, config = setup_kis_client('demo')

# 시장가 조회 및 출력
market_info = client.get_market_price("005930")
print_market_info(market_info)
```

[자세한 문서](kis_app_utils.md)

### config_loader.py
설정 파일을 로드하고 관리하는 모듈

**주요 기능:**
- JSON 설정 파일 로드
- 중첩된 키 경로로 값 조회
- KIS API 설정 관리

**사용 예제:**
```python
from config_loader import get_config

config = get_config()
kis_config = config.get_kis_config('demo')
```

[자세한 문서](config_loader.md)

### kis_auth.py
한국투자증권 API 인증 처리 모듈

**주요 기능:**
- OAuth 2.0 토큰 발급
- 토큰 저장/로드
- API 호출 헤더 생성

**사용 예제:**
```python
from kis_auth import KISAuth

auth = KISAuth(
    appkey="...",
    appsecret="...",
    account="...",
    env='demo'
)
token = auth.authenticate()
```

[자세한 문서](kis_auth.md)

### kis_api_client.py
KIS API 클라이언트 래퍼 모듈

**주요 기능:**
- 주식 현재가 조회
- 시장가 정보 조회
- API 호출 공통 처리

**사용 예제:**
```python
from kis_api_client import KISAPIClient

client = KISAPIClient(auth)
df = client.inquire_price("005930")
```

[자세한 문서](kis_api_client.md)

## 애플리케이션

### samsung_price_inquiry.py
삼성전자 시장가 조회 애플리케이션

**기능:**
- 삼성전자(005930) 현재가 조회
- 포맷팅된 결과 출력
- 에러 처리

[자세한 문서](samsung_price_inquiry.md)

## 사용 예제

### 기본 시세 조회 (간편 버전)

```python
from kis_app_utils import setup_kis_client, print_market_info

# 클라이언트 자동 설정
client, _ = setup_kis_client('demo')

# 시세 조회 및 출력
market_info = client.get_market_price("005930")
print_market_info(market_info)
```

### 기본 시세 조회 (상세 버전)

```python
from config_loader import get_config
from kis_auth import KISAuth
from kis_api_client import KISAPIClient

# 설정 로드
config = get_config()
kis_config = config.get_kis_config('demo')

# 인증
auth = KISAuth(
    appkey=kis_config['appkey'],
    appsecret=kis_config['appsecret'],
    account=kis_config['account'],
    env='demo'
)
auth.authenticate()

# API 클라이언트
client = KISAPIClient(auth)

# 시세 조회
market_info = client.get_market_price("005930")
print(f"{market_info['종목명']}: {int(market_info['현재가']):,}원")
```

### 여러 종목 조회

```python
stocks = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "035420": "NAVER",
    "035720": "카카오"
}

for code, name in stocks.items():
    market_info = client.get_market_price(code)
    if market_info:
        print(f"{name}: {int(market_info['현재가']):,}원 ({market_info['등락률']}%)")
```

## API 제한사항

### 호출 제한
- 초당 API 호출 횟수 제한 있음
- 과도한 호출 시 일시적으로 차단될 수 있음

### 시세 데이터
- REST API는 실시간이 아님
- 실시간 시세는 WebSocket API 사용 권장
- 장 운영 시간 외에는 전일 종가 조회

### 토큰 관리
- 토큰 유효기간: 24시간
- 6시간 이내 재발급 시 기존 토큰 재사용
- 발급 시 알림톡 발송 (실전투자)

## 주의사항

### 보안
- ⚠️ **API 키를 절대 코드에 하드코딩하지 마세요**
- ⚠️ **config.json 파일을 Git에 커밋하지 마세요**
- `.gitignore`에 `Config/config.json` 추가 권장

### 테스트
- ✅ 실전투자 전에 **반드시 모의투자로 충분히 테스트**
- ✅ 모의투자 환경(`env='demo'`)에서 먼저 검증

### 법적 책임
- 본 프로젝트는 교육/학습 목적입니다
- 실제 투자로 인한 손실에 대한 책임은 사용자에게 있습니다

## 개발 로드맵

### 완료된 기능
- [x] 설정 파일 관리
- [x] KIS API 인증
- [x] 현재가 조회
- [x] 기본 문서화

### 향후 계획
- [ ] 주식 주문 (매수/매도)
- [ ] 계좌 잔고 조회
- [ ] 호가 조회
- [ ] 일자별 시세 조회
- [ ] WebSocket 실시간 시세
- [ ] 자동매매 전략
- [ ] 백테스팅 기능
- [ ] GUI 인터페이스

## 문제 해결

### 설정 파일을 찾을 수 없음
```
FileNotFoundError: 설정 파일을 찾을 수 없습니다
```
→ `Config/config.json` 파일이 있는지 확인

### 인증 실패
```
Exception: 인증 실패: 401
```
→ appkey, appsecret이 올바른지 확인

### 모듈을 찾을 수 없음
```
ModuleNotFoundError: No module named 'config_loader'
```
→ `Scripts/apps/` 디렉토리에서 실행하고 있는지 확인

### 토큰 만료
```bash
# 토큰 파일 삭제 후 재실행
# Windows
Remove-Item -Recurse -Force "$env:USERPROFILE\KIS\config\KIS_*"

# Linux/Mac
rm -rf ~/KIS/config/KIS_*
```

## 참고 자료

### 공식 문서
- [한국투자증권 Open Trading API](https://apiportal.koreainvestment.com/)
- [KIS Developers GitHub](https://github.com/koreainvestment/open-trading-api)

### 관련 문서
- [kis_app_utils 모듈](kis_app_utils.md) - 공통 유틸리티
- [config_loader 모듈](config_loader.md)
- [kis_auth 모듈](kis_auth.md)
- [kis_api_client 모듈](kis_api_client.md)
- [samsung_price_inquiry 앱](samsung_price_inquiry.md)

## 라이선스
이 프로젝트는 교육 및 학습 목적으로 제공됩니다.

## 기여
버그 리포트, 기능 제안, Pull Request 환영합니다.

## 연락처
문의사항이 있으시면 이슈를 등록해주세요.
