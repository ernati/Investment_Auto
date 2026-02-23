# 웹 브라우저 DB 데이터 확인 스크립트 문서

## 개요

`test_web_db.py` 스크립트는 Investment_Auto 웹 인터페이스의 데이터베이스 탭이 정상적으로 작동하는지 검증하는 도구입니다. 
웹 서버 상태 확인부터 각 DB API 엔드포인트 테스트까지 종합적인 검증을 수행합니다.

## 주요 기능

### 1. 웹 서버 상태 확인
- 서버 연결 상태 확인
- 헬스 체크 API 호출
- API 및 DB 연결 상태 검증
- 환경 설정 확인

### 2. DB API 엔드포인트 테스트
- **거래 기록 API**: `/api/db/trading-history` 테스트
- **리밸런싱 로그 API**: `/api/db/rebalancing-logs` 테스트  
- **포트폴리오 스냅샷 API**: `/api/db/portfolio-snapshots` 테스트
- **시스템 로그 API**: `/api/db/system-logs` 테스트

### 3. 데이터 검증
- API 응답 상태 코드 확인
- JSON 데이터 구조 검증
- 데이터 건수 확인
- 응답 시간 측정

### 4. 사용자 가이드 제공
- 웹 브라우저 사용법 안내
- 기능별 체크리스트 제공
- 문제 해결 가이드 포함

## 함수 구조

### check_web_server_status(base_url) → bool
웹 서버의 상태를 확인합니다.

**확인 항목:**
- 서버 연결 가능 여부
- 헬스 체크 API 응답  
- 환경 설정 (demo/real)
- KIS API 연결 상태
- 데이터베이스 연결 상태

**반환값:** 서버 정상 시 True, 문제 시 False

**출력 예시:**
```
🔍 웹 서버 상태 확인...
  ✅ 서버 상태: healthy
  🌐 환경: demo
  📡 API 상태: connected
  🗄️ DB 상태: connected
```

### test_web_api(base_url) → bool
모든 DB API 엔드포인트를 테스트합니다.

**테스트 API:**
- 거래 기록: `portfolio_id=demo_portfolio&limit=5`
- 리밸런싱 로그: `portfolio_id=demo_portfolio&limit=5`  
- 포트폴리오 스냅샷: `portfolio_id=demo_portfolio&limit=5`
- 시스템 로그: `limit=5`

**검증 내용:**
- HTTP 상태 코드 (200 OK)
- JSON 응답 구조
- 에러 메시지 유무
- 데이터 건수
- 응답 필드 구조

**반환값:** 모든 API 정상 시 True, 하나라도 실패 시 False

**출력 예시:**
```
🌐 웹 API 테스트 시작
============================================================
💰 거래 기록 테스트...
  ✅ 성공: 5건 조회됨
  📄 첫 번째 레코드: ['commission', 'environment', 'id', 'order_id', 'order_type']...
⚖️ 리밸런싱 로그 테스트...
  ✅ 성공: 3건 조회됨
  📄 첫 번째 레코드: ['after_weights', 'before_weights', 'environment', 'error_message', 'id']...
```

## 사용법

### 기본 실행
```bash
cd d:\dev\repos\Investment_Auto\Scripts\tests
python test_web_db.py
```

### 실행 조건
1. **웹 서버 실행 필요**
   ```bash
   cd d:\dev\repos\Investment_Auto\Scripts\apps
   python portfolio_web_app.py --env demo --port 5001
   ```

2. **테스트 데이터 존재**
   ```bash
   python insert_test_data.py  # 테스트 데이터 생성
   python verify_test_data.py  # 데이터 존재 확인
   ```

3. **PostgreSQL 서버 실행**
   - 데이터베이스 서비스 상태 확인
   - `Config/database.json` 설정 점검

## 실행 결과

### 성공 케이스
```
✅ 모든 API가 정상 작동합니다!
💻 웹 브라우저에서 확인: http://127.0.0.1:5001
🗄️ '데이터베이스' 탭을 클릭하여 DB 데이터를 확인하세요.

🎉 모든 준비 완료!
🌐 웹 브라우저에서 http://127.0.0.1:5001 접속
📋 체크리스트:
  1. 🗄️ '데이터베이스' 탭 클릭
  2. 💰 '거래 기록' 서브탭에서 15건 데이터 확인 
  3. ⚖️ '리밸런싱 로그' 서브탭에서 3건 데이터 확인
  4. 📊 '포트폴리오 스냅샷' 서브탭에서 10건 데이터 확인
  5. 📋 '시스템 로그' 서브탭에서 21건 데이터 확인
  6. 🔍 각 탭에서 필터링 및 리셋 버튼 테스트
  7. 📄 페이지네이션 (이전/다음) 버튼 테스트
```

### 실패 케이스

#### 웹 서버 미실행
```
🔍 웹 서버 상태 확인...
  ❌ 서버 연결 실패: http://127.0.0.1:5001
  💡 웹 서버가 실행 중인지 확인하세요:
     python portfolio_web_app.py --env demo --port 5001
```

#### API 에러
```
💰 거래 기록 테스트...
  ❌ API 에러: Database not available

⚠️ 일부 API에 문제가 있습니다.
🔧 웹 서버 상태와 데이터베이스 연결을 확인해주세요.
```

#### 데이터 없음
```
📊 포트폴리오 스냅샷 테스트...
  ✅ 성공: 0건 조회됨

💡 테스트 데이터가 없는 경우:
   python insert_test_data.py
```

## 에러 처리

### ConnectionError
- **원인**: 웹 서버가 실행되지 않거나 포트가 다름
- **해결**: `portfolio_web_app.py` 실행 상태 확인

### Timeout  
- **원인**: 서버 응답 지연 (5초 이상)
- **해결**: 서버 성능 확인, 데이터베이스 연결 점검

### HTTP 4xx/5xx 에러
- **원인**: API 내부 오류, 잘못된 파라미터
- **해결**: 서버 로그 확인, API 파라미터 점검

### JSON 파싱 에러
- **원인**: 응답 데이터 형식 문제
- **해결**: API 응답 구조 확인, 서버 로직 점검

## 설정값

### 기본 URL
```python
base_url = "http://127.0.0.1:5001"
```

### API 테스트 파라미터
```python
test_apis = [
    {
        "name": "거래 기록",
        "url": f"{base_url}/api/db/trading-history?portfolio_id=demo_portfolio&limit=5",
        "icon": "💰"
    },
    # ... 다른 API들
]
```

### 타임아웃 설정
- **헬스 체크**: 5초
- **API 테스트**: 10초
- **API 호출 간격**: 0.5초

## 확장 기능

### 성능 측정  
API 응답 시간을 측정하여 성능을 모니터링할 수 있습니다.

```python
import time
start_time = time.time()
response = requests.get(api['url'], timeout=10)
response_time = time.time() - start_time
print(f"  ⏱️ 응답 시간: {response_time:.3f}초")
```

### 상세 데이터 검증
첫 번째 레코드의 필드값을 검증하여 데이터 품질을 확인할 수 있습니다.

```python
if record_count > 0:
    first_record = data['data'][0]
    # 필수 필드 존재 여부 확인
    required_fields = ['id', 'timestamp', 'environment']
    missing_fields = [f for f in required_fields if f not in first_record]
    if missing_fields:
        print(f"  ⚠️ 누락된 필드: {missing_fields}")
```

### 자동화 통합
CI/CD 파이프라인에 통합하여 자동 테스트를 수행할 수 있습니다.

```bash
# GitHub Actions 예시
- name: Test Web DB Interface  
  run: |
    python Scripts/apps/portfolio_web_app.py --env demo &
    sleep 5
    python Scripts/tests/test_web_db.py
    pkill -f portfolio_web_app.py
```

## 의존성

### 내부 모듈
- 없음 (독립 실행 가능)

### 외부 라이브러리
- `requests`: HTTP API 호출
- `json`: JSON 데이터 파싱
- `time`: 응답 시간 측정
- `sys`: 프로그램 종료 코드

### 서비스 의존성
- **웹 서버**: `portfolio_web_app.py` 실행 필요
- **PostgreSQL**: 데이터베이스 서버 실행
- **테스트 데이터**: `insert_test_data.py`로 생성

## 모니터링

### 정기 실행
스크립트를 정기적으로 실행하여 서비스 상태를 모니터링할 수 있습니다.

```bash
# 매시 정각에 실행 (cron 예시)
0 * * * * cd /path/to/Investment_Auto/Scripts/tests && python test_web_db.py
```

### 알림 연동
테스트 실패 시 알림을 보내도록 확장할 수 있습니다.

```python
import smtplib
from email.mime.text import MIMEText

def send_alert(message):
    msg = MIMEText(message)
    msg['Subject'] = '웹 DB 인터페이스 테스트 실패'
    # SMTP 서버를 통한 이메일 발송
```

### 로그 수집
테스트 결과를 로그 파일에 저장하여 이력을 관리할 수 있습니다.

```python
import logging

# 파일 로그 핸들러 추가
file_handler = logging.FileHandler('web_db_test.log')
logger.addHandler(file_handler)
```

## 워크플로우

### 최초 설정 시
1. **데이터베이스 준비**: PostgreSQL 설치 및 설정
2. **테스트 데이터 생성**: `insert_test_data.py` 실행
3. **웹 서버 시작**: `portfolio_web_app.py` 실행  
4. **테스트 실행**: `test_web_db.py` 실행
5. **브라우저 확인**: 수동으로 웹 인터페이스 검증

### 정기 점검 시
1. **자동 테스트**: `test_web_db.py` 실행
2. **결과 확인**: 성공/실패 상태 점검
3. **문제 해결**: 실패 시 로그 분석 및 수정
4. **재테스트**: 수정 후 다시 테스트

### 배포 전 검증
1. **코드 변경**: 웹 인터페이스 수정
2. **서버 재시작**: 새 코드 적용
3. **테스트 실행**: 회귀 테스트 수행
4. **성능 확인**: 응답 시간 및 안정성 검증
5. **사용자 테스트**: 실제 브라우저에서 기능 확인

## 관련 파일

- `portfolio_web_app.py`: 웹 애플리케이션 메인 런처
- `web_server.py`: 웹 서버 구현 및 DB API
- `insert_test_data.py`: 테스트 데이터 생성
- `verify_test_data.py`: 테스트 데이터 검증
- `db_manager.py`: 데이터베이스 연결 및 쿼리
- `Config/database.json`: 데이터베이스 설정

## 다음 단계

테스트 성공 후:
1. **브라우저 접속**: http://127.0.0.1:5001
2. **DB 탭 확인**: 각 서브탭별 데이터 출력 검증
3. **필터링 테스트**: 다양한 필터 조건 적용
4. **성능 확인**: 대용량 데이터 처리 테스트
5. **사용자 매뉴얼**: 실제 사용자를 위한 가이드 작성

정기적으로 이 스크립트를 실행하여 웹 인터페이스의 안정성을 보장하고, 문제 발생 시 신속하게 대응할 수 있습니다.