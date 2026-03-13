# DB/Web 진단 스크립트 문서

## 개요

`db_web_diagnostic.py`는 운영 서버에서 웹을 통해 DB 데이터가 보이지 않을 때, 문제의 원인을 파악하기 위한 진단 도구입니다.

다음 세 가지 문제 중 어디에 해당하는지 구분할 수 있습니다:
1. **DB에 데이터가 없는 경우**
2. **Web 서버가 DB 데이터를 못 가져오는 경우**
3. **Web을 통해 보는 방법이 잘못된 경우**

## 파일 위치

```
Investment_Auto/
└── Scripts/
    └── tests/
        └── db_web_diagnostic.py
```

## 의존성

```bash
pip install psycopg2-binary requests
```

## 사용법

### 기본 실행 (전체 진단)

```bash
cd d:\dev\repos\Investment_Auto
python Scripts/tests/db_web_diagnostic.py --all
```

### DB만 테스트

```bash
python Scripts/tests/db_web_diagnostic.py --db-only
```

### Web만 테스트

```bash
python Scripts/tests/db_web_diagnostic.py --web-only
```

### SQL 쿼리 확인

DB에 직접 접속해서 확인할 때 사용할 쿼리들을 출력합니다.

```bash
python Scripts/tests/db_web_diagnostic.py --show-queries
```

### Web API 엔드포인트 확인

웹 API 엔드포인트 목록과 cURL 명령어를 출력합니다.

```bash
python Scripts/tests/db_web_diagnostic.py --show-endpoints
```

## 환경 변수로 설정 덮어쓰기

운영 서버의 DB나 Web 서버가 다른 호스트에 있을 때:

```bash
# DB 설정 변경
DB_HOST=production-db.example.com DB_PORT=5432 python Scripts/tests/db_web_diagnostic.py --db-only

# Web 서버 설정 변경
WEB_HOST=192.168.1.100 WEB_PORT=8080 python Scripts/tests/db_web_diagnostic.py --web-only
```

## 진단 항목

### DB 진단 (Database)

| 테스트 항목 | 설명 |
|------------|------|
| psycopg2 패키지 | 데이터베이스 드라이버 설치 여부 |
| 설정 파일 로드 | `Config/database.json` 파일 로드 |
| DB 연결 | PostgreSQL 연결 테스트 |
| 테이블 존재 | 필수 테이블 존재 여부 |
| 각 테이블 데이터 | 테이블별 레코드 수 확인 |
| db_manager 모듈 | Python 모듈 임포트 |
| DatabaseManager 연결 | 앱 레벨 연결 테스트 |

### Web 진단 (Web Server)

| 테스트 항목 | 설명 |
|------------|------|
| requests 패키지 | HTTP 클라이언트 설치 여부 |
| 서버 포트 연결 | 웹 서버 실행 여부 |
| 메인 페이지 | 메인 페이지 로드 |
| 헬스 체크 API | `/health` 엔드포인트 |
| 거래 기록 API | `/api/db/trading-history` |
| 포트폴리오 스냅샷 API | `/api/db/portfolio-snapshots` |
| 리밸런싱 로그 API | `/api/db/rebalancing-logs` |

## 출력 예시

### 모두 정상인 경우

```
======================================================================
📋 DB/Web 진단 결과 요약
======================================================================
시각: 2026-03-14T10:30:00

📂 Database
--------------------------------------------------
  ✅ psycopg2 패키지
      └─ psycopg2 버전: 2.9.9
  ✅ 설정 파일 로드
      └─ 설정 파일 로드 성공
  ✅ DB 연결
      └─ 연결 성공! (host=localhost, db=appdb)
  ✅ 테이블 존재
      └─ 모든 필수 테이블 존재: ['trading_history', ...]
  ✅ 'trading_history' 데이터
      └─ 테이블 'trading_history'에 150개 레코드 존재

📂 Web Server
--------------------------------------------------
  ✅ 서버 포트 연결
      └─ 웹 서버 포트 5000 열려있음
  ✅ 헬스 체크 API
      └─ 헬스 체크 성공 (db=connected, api=connected)

======================================================================
📊 결과: 10/10 테스트 통과

✅ 모든 테스트 통과! DB와 Web 연결이 정상입니다.
======================================================================
```

### 문제가 있는 경우

```
======================================================================
📊 결과: 7/10 테스트 통과

⚠️  경고 (1개):
    - 헬스 체크에서 DB 상태: disconnected

❌ 오류 (3개):
    - [Database] DB 연결: 연결 실패: connection refused
    - [Database] 'trading_history' 데이터: 테이블 확인 실패

💡 문제 해결 방법:
    1. DB 서버가 실행 중인지 확인: PostgreSQL 서비스 상태 확인
    2. DB 설정 확인: Config/database.json의 host, port, user, password 검증
    3. 방화벽/네트워크 확인: 해당 포트(5432)가 열려있는지 확인
======================================================================
```

## 문제별 해결 방법

### 1. DB 연결 실패

```
❌ DB 연결: 연결 실패: connection refused
```

**확인 사항:**
- PostgreSQL 서비스가 실행 중인지 확인
- `Config/database.json`의 host, port, user, password 확인
- 방화벽에서 5432 포트가 열려있는지 확인
- 원격 접속 허용 설정 (pg_hba.conf)

### 2. 테이블이 없음

```
❌ 테이블 존재: 누락된 테이블: ['trading_history', ...]
```

**해결:**
```python
from Scripts.modules.db_manager import DatabaseManager
db = DatabaseManager()
db.create_tables()
```

### 3. 데이터가 없음

```
✅ 'trading_history' 데이터
   └─ 테이블 'trading_history'에 데이터 없음 (0 rows)
```

**원인:**
- 아직 거래나 리밸런싱이 실행되지 않음
- 데이터가 다른 environment(demo/real)에 저장됨

**확인:**
```bash
python Scripts/tests/db_web_diagnostic.py --show-queries
```

### 4. Web 서버 연결 불가

```
❌ 서버 포트 연결: 웹 서버 포트 5000에 연결 불가
```

**해결:**
```bash
python Scripts/apps/portfolio_web_app.py
```

### 5. API에서 "Database not available" 반환

```
❌ 거래 기록 API: API 오류: HTTP 500 - {"error": "Database not available"}
```

**원인:**
- 웹 서버 시작 시 DB 연결 실패
- `web_server.py`에서 `self.db_manager = None`으로 설정됨

**해결:**
1. 먼저 DB 연결 문제 해결
2. 웹 서버 재시작

## 관련 파일

| 파일 | 설명 |
|------|------|
| `Config/database.json` | DB 연결 설정 |
| `Scripts/modules/db_manager.py` | DB 관리 모듈 |
| `Scripts/modules/web_server.py` | 웹 서버 모듈 |
| `Scripts/apps/portfolio_web_app.py` | 웹 앱 실행 스크립트 |

## 주의사항

1. **운영 환경에서 실행 시**: 환경 변수로 올바른 호스트 지정 필요
2. **보안**: 진단 결과에 민감한 정보(비밀번호 등)가 포함될 수 있으므로 주의
3. **네트워크**: 로컬 환경과 운영 환경의 네트워크 설정이 다를 수 있음
