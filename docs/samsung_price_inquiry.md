# samsung_price_inquiry.py 애플리케이션 문서

## 개요
삼성전자(005930) 주식의 현재 시장가 정보를 조회하는 애플리케이션입니다. 한국투자증권 Open Trading API를 사용합니다.

## 주요 기능
- 삼성전자 현재가 조회
- 전일대비, 등락률 확인
- 시가, 고가, 저가 정보 제공
- 거래량, 거래대금 정보 제공
- 실전투자/모의투자 환경 지원

## 파일 위치
```
Investment_Auto/
└── Scripts/
    └── apps/
        └── samsung_price_inquiry.py
```

## 의존성

### 모듈
- `kis_app_utils`: 공통 유틸리티 (클라이언트 설정, 출력 포맷팅, 에러 처리)
  - `setup_kis_client`: 자동 클라이언트 설정
  - `print_header`: 헤더 출력
  - `print_market_info`: 시장가 정보 출력
  - `handle_common_errors`: 에러 처리 데코레이터
  - `ProgressPrinter`: 진행 상황 출력

간접적으로 사용되는 모듈 (kis_app_utils를 통해):
- `config_loader`: 설정 파일 로드
- `kis_auth`: KIS API 인증
- `kis_api_client`: KIS API 클라이언트

### Python 패키지
- `pandas`: 데이터 처리
- `requests`: HTTP 요청

## 실행 방법

### 1. 설정 파일 구성
먼저 `Config/config.json` 파일을 작성합니다:

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

### 2. 실행

#### Windows (PowerShell)
```powershell
cd d:\dev\repos\Investment_Auto\Scripts\apps
python samsung_price_inquiry.py
```

#### Linux/Mac
```bash
cd /path/to/Investment_Auto/Scripts/apps
python3 samsung_price_inquiry.py
```

## 출력 예시

```
============================================================
삼성전자 시장가 조회
============================================================

[1] 설정 파일 로드 중...
   - 환경: demo
   - 계좌: 12345678

[2] API 인증 중...
   - 인증 완료 (토큰 발급됨)

[3] API 클라이언트 초기화...

[4] 삼성전자(005930) 시장가 조회 중...

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

[상세 데이터]
    prdt_name  stck_prpr  prdy_vrss  ...
0   삼성전자     71000      1000      ...
```

## 코드 구조

### main() 함수
메인 실행 함수로 다음 단계로 구성됩니다:

1. **진행 상황 출력 헬퍼 생성**
   - `ProgressPrinter`를 사용하여 단계별 진행 상황 표시

2. **클라이언트 설정**
   - `setup_kis_client()`를 사용하여 자동 설정
   - 설정 로드, 인증, 클라이언트 생성을 한 번에 처리

3. **시장가 조회**
   - `inquire_price()`: 전체 데이터 조회
   - `get_market_price()`: 주요 정보 추출

4. **결과 출력**
   - `print_market_info()`: 포맷팅된 결과 출력
   - 상세 데이터 출력 (선택사항)

### 공통 유틸리티 사용
이 앱은 `kis_app_utils` 모듈의 공통 유틸리티를 사용합니다:
- `setup_kis_client()`: 클라이언트 자동 설정
- `print_header()`: 헤더 출력
- `print_market_info()`: 시장가 정보 포맷팅
- `handle_common_errors`: 에러 처리 데코레이터
- `ProgressPrinter`: 진행 상황 출력

이를 통해 코드 중복을 제거하고 일관성을 유지합니다.

## 코드 수정 가이드

### 환경 변경 (모의투자 ↔ 실전투자)

코드의 다음 부분에서 환경을 선택합니다:

```python
# 실전/모의 환경 선택 (기본값: real)
env = 'real'  # 'real' 또는 'demo'
```

**실전투자 (기본값):**
```python
env = 'real'
```

**모의투자 (테스트용):**
```python
env = 'demo'
```

⚠️ **주의**: 기본값이 'real' (실전 계좌)로 설정되어 있습니다.

### 다른 종목 조회

삼성전자 대신 다른 종목을 조회하려면:

```python
# 삼성전자 시장가 조회
stock_code = "005930"  # 삼성전자
```

다음과 같이 변경:

```python
# SK하이닉스 시장가 조회
stock_code = "000660"  # SK하이닉스
```

**주요 종목 코드:**
- 삼성전자: 005930
- SK하이닉스: 000660
- NAVER: 035420
- 카카오: 035720
- LG에너지솔루션: 373220

### 출력 형식 변경

더 간단한 출력:

```python
if market_info:
    print(f"{market_info['종목명']}: {int(market_info['현재가']):,}원 ({market_info['등락률']}%)")
```

CSV 형식 출력:

```python
if market_info:
    print(f"{market_info['종목코드']},{market_info['종목명']},{market_info['현재가']},{market_info['등락률']}")
```

## 에러 처리

### FileNotFoundError
```
오류: 설정 파일을 찾을 수 없습니다: ...

설정 파일(Config/config.json)을 확인해주세요.
```

**해결 방법:**
1. `Config/config.json` 파일이 있는지 확인
2. 파일 경로가 올바른지 확인

### ValueError
```
오류: KIS 설정을 찾을 수 없습니다: demo
```

**해결 방법:**
1. `config.json`에 해당 환경(`real` 또는 `demo`) 설정이 있는지 확인
2. JSON 형식이 올바른지 확인

### API 인증 오류
```
예상치 못한 오류 발생: 인증 실패: 401, ...
```

**해결 방법:**
1. `appkey`와 `appsecret`이 올바른지 확인
2. 실전투자/모의투자 키를 올바르게 사용했는지 확인
3. 한국투자증권 홈페이지에서 키 상태 확인

### API 호출 오류
```
예상치 못한 오류 발생: API 오류: [EGW00123] ...
```

**해결 방법:**
1. 장 운영 시간 확인 (09:00~15:30)
2. 종목코드가 올바른지 확인
3. API 호출 제한 확인

## 활용 예제

### 1. 여러 종목 조회

```python
def main():
    # ... 설정 및 인증 코드 ...
    
    client = KISAPIClient(auth)
    
    # 여러 종목 조회
    stocks = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
    
    for stock_code in stocks:
        market_info = client.get_market_price(stock_code)
        if market_info:
            print(f"{market_info['종목명']}: {int(market_info['현재가']):,}원 ({market_info['등락률']}%)")
```

### 2. 특정 조건 체크

```python
def main():
    # ... 설정 및 인증 코드 ...
    
    client = KISAPIClient(auth)
    market_info = client.get_market_price("005930")
    
    if market_info:
        current_price = int(market_info['현재가'])
        change_rate = float(market_info['등락률'])
        
        # 등락률이 2% 이상이면 알림
        if abs(change_rate) >= 2.0:
            print(f"주목! {market_info['종목명']} 등락률 {change_rate}%")
```

### 3. CSV 저장

```python
import csv
from datetime import datetime

def main():
    # ... 설정 및 인증 코드 ...
    
    client = KISAPIClient(auth)
    market_info = client.get_market_price("005930")
    
    if market_info:
        # CSV 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"samsung_price_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['종목코드', '종목명', '현재가', '등락률', '거래량'])
            writer.writerow([
                market_info['종목코드'],
                market_info['종목명'],
                market_info['현재가'],
                market_info['등락률'],
                market_info['거래량']
            ])
        
        print(f"결과 저장: {filename}")
```

### 4. 주기적 조회

```python
import time

def main():
    # ... 설정 및 인증 코드 ...
    
    client = KISAPIClient(auth)
    
    # 10초마다 조회 (5회)
    for i in range(5):
        market_info = client.get_market_price("005930")
        if market_info:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {market_info['종목명']}: {int(market_info['현재가']):,}원")
        
        if i < 4:  # 마지막 반복에서는 대기하지 않음
            time.sleep(10)
```

## 개선 아이디어

1. **명령행 인자 지원**
   ```python
   import argparse
   
   parser = argparse.ArgumentParser()
   parser.add_argument('--stock', default='005930', help='종목코드')
   parser.add_argument('--env', default='real', choices=['real', 'demo'])
   args = parser.parse_args()
   ```

2. **로깅 추가**
   ```python
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(levelname)s - %(message)s',
       filename='stock_inquiry.log'
   )
   ```

3. **GUI 추가**
   - Tkinter, PyQt 등을 사용한 GUI 인터페이스

4. **데이터베이스 저장**
   - SQLite, MySQL 등에 시세 데이터 저장

5. **알림 기능**
   - 특정 조건 달성 시 이메일/SMS 알림

## 주의사항

1. **보안**: API 키는 절대 코드에 하드코딩하지 마세요.
2. **테스트**: 실전투자 전에 반드시 모의투자로 충분히 테스트하세요.
3. **API 제한**: 초당 호출 횟수 제한을 준수하세요.
4. **장 운영 시간**: 장 운영 시간 외에는 전일 데이터가 조회됩니다.

## 문제 해결

### 토큰 관련 오류
토큰이 만료되었거나 문제가 있다면:

```powershell
# Windows
Remove-Item -Recurse -Force "$env:USERPROFILE\KIS\config\KIS_*"

# Linux/Mac
rm -rf ~/KIS/config/KIS_*
```

다시 실행하면 새 토큰이 발급됩니다.

### 모듈을 찾을 수 없음
```
ModuleNotFoundError: No module named 'config_loader'
```

**해결 방법:**
- 스크립트를 `Scripts/apps/` 디렉토리에서 실행하고 있는지 확인
- 모듈 파일들이 `Scripts/modules/`에 있는지 확인

## 참고 자료

- [한국투자증권 Open Trading API](https://apiportal.koreainvestment.com/)
- [KIS Developers GitHub](https://github.com/koreainvestment/open-trading-api)
- 관련 문서:
  - [config_loader.md](config_loader.md)
  - [kis_auth.md](kis_auth.md)
  - [kis_api_client.md](kis_api_client.md)
