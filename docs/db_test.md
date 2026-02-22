# db_test.py 모듈 문서

## 개요

`db_test.py`는 Investment_Auto 시스템의 데이터베이스 연결 및 데이터 확인을 위한 전용 테스트 스크립트입니다. kis_debug.py의 데이터베이스 테스트 부분만을 분리하여 단순하고 빠르게 DB 상태를 확인할 수 있습니다.

## 파일 위치
`Scripts/tests/db_test.py`

## 주요 기능

### 1. 데이터베이스 연결 테스트
- DatabaseManager를 통한 PostgreSQL 연결 확인
- 자동 테이블 생성 및 초기화
- 연결 실패 시 원인 진단 정보 제공

### 2. 테이블별 데이터 현황 조회
- **trading_history**: 거래 기록 개수 및 최근 3건 출력
- **rebalancing_logs**: 리밸런싱 로그 개수 및 최근 2건 출력  
- **portfolio_snapshots**: 포트폴리오 스냅샷 개수 및 최근 2건 출력
- **system_logs**: 시스템 로그는 개수만 확인

### 3. 테스트 데이터 생성
- 샘플 거래 기록 생성 및 저장
- 샘플 시스템 로그 생성 및 저장
- 저장 성공/실패 확인

## 사용 방법

### 실행 명령어

```bash
# Investment_Auto 프로젝트 루트에서 실행
python Scripts/tests/db_test.py

# 또는 tests 디렉토리에서 실행
cd Scripts/tests
python db_test.py
```

### 실행 결과 예시

#### 성공적인 실행 (데이터 있음)
```
🗃️ 데이터베이스 연결 및 데이터 확인 테스트
============================================================
📡 데이터베이스 연결 중...
✅ 데이터베이스 연결 성공

📋 테이블별 데이터 현황:
  📈 거래 기록: 15건
     최근 3건:
       1. 2026-02-22 10:30:15 | 005930 buy 100주 @ 75,000원
       2. 2026-02-22 09:15:30 | 035420 sell 50주 @ 225,000원  
       3. 2026-02-21 15:45:00 | 000660 buy 200주 @ 85,000원

  ⚖️ 리밸런싱 로그: 3건
     최근 2건:
       1. 2026-02-22 09:00:00 | success | 5건 | Scheduled rebalancing...
       2. 2026-02-21 09:00:00 | success | 2건 | Threshold deviation...

  📸 포트폴리오 스냅샷: 48건
     최근 2건:
       1. 2026-02-22 10:00:00 | 총자산: 15,000,000원 | 포지션: 5개
       2. 2026-02-21 18:00:00 | 총자산: 14,850,000원 | 포지션: 4개

🧪 테스트 데이터 생성:
  ✅ 샘플 거래 기록 저장 성공
  ✅ 샘플 시스템 로그 저장 성공

✅ 데이터베이스 테스트 완료!
ℹ️ 데이터가 없는 것은 정상입니다 (시스템이 아직 거래를 수행하지 않음)
```

#### 초기 설치 상태 (데이터 없음)
```
🗃️ 데이터베이스 연결 및 데이터 확인 테스트
============================================================
📡 데이터베이스 연결 중...
✅ 데이터베이스 연결 성공

📋 테이블별 데이터 현황:
  📈 거래 기록: 0건
     ⚠️ 데이터 없음 (정상 - 거래 기록이 아직 없음)

  ⚖️ 리밸런싱 로그: 0건  
     ⚠️ 데이터 없음 (정상 - 리밸런싱 실행 기록이 없음)

  📸 포트폴리오 스냅샷: 0건
     ⚠️ 데이터 없음 (정상 - 포트폴리오 스냅샷이 없음)

🧪 테스트 데이터 생성:
  ✅ 샘플 거래 기록 저장 성공
  ✅ 샘플 시스템 로그 저장 성공

✅ 데이터베이스 테스트 완료!
ℹ️ 데이터가 없는 것은 정상입니다 (시스템이 아직 거래를 수행하지 않음)
```

#### 실패 시나리오 (DB 연결 불가)
```
🗃️ 데이터베이스 연결 및 데이터 확인 테스트
============================================================
📡 데이터베이스 연결 중...
❌ 데이터베이스 초기화 실패
💡 확인사항:
   - PostgreSQL 서비스가 실행 중인가요?
   - Config/database.json 설정이 올바른가요?
   - 데이터베이스 사용자 권한이 있나요?
```

## 장점

### 1. 단순성
- KIS API 의존성 없음
- 데이터베이스만 집중 테스트
- 빠른 실행 시간

### 2. 명확한 출력
- 컬러 이모지로 직관적 결과 표시
- 구체적인 데이터 샘플 출력
- 에러 원인 진단 정보 제공

### 3. Safe Testing
- demo 환경에서만 테스트 데이터 생성
- 기존 데이터 손상 없음
- 읽기 전용 조회가 주요 기능

## 활용 시나리오

### 1. 개발 환경 설정 후
```bash
# 새 개발 환경에서 DB 설정 확인
python Scripts/tests/db_test.py
```

### 2. 배포 후 검증
```bash
# 운영 서버 배포 후 DB 연결 상태 확인
python Scripts/tests/db_test.py
```

### 3. 정기 모니터링
```bash
# 매일 아침 DB 상태 점검
python Scripts/tests/db_test.py
```

### 4. 문제 진단
```bash
# 시스템 오류 발생 시 DB 상태 우선 확인
python Scripts/tests/db_test.py
```

## 에러 처리

### 연결 실패 시 확인사항

1. **PostgreSQL 서비스 상태**
   ```bash
   # Windows
   services.msc에서 PostgreSQL 서비스 확인
   
   # Linux/Mac  
   sudo systemctl status postgresql
   ```

2. **database.json 설정**
   ```json
   {
       "database": {
           "host": "localhost",
           "port": 5432,
           "name": "appdb",
           "user": "appuser",
           "password": "your_password"
       }
   }
   ```

3. **사용자 권한**
   ```sql
   -- PostgreSQL에서 권한 확인
   \du appuser
   
   -- 권한 부여
   GRANT ALL PRIVILEGES ON DATABASE appdb TO appuser;
   ```

### 로그 확인

실패 시 자세한 로그는 다음 위치에서 확인:
- 애플리케이션 로그: `logs/` 디렉토리
- PostgreSQL 로그: 시스템 로그 디렉토리

## 구성 파일

### 의존성
- `modules.db_manager`: DatabaseManager 클래스
- `modules.db_models`: 데이터 모델 클래스  
- `Config/database.json`: 데이터베이스 설정

### 테스트 데이터

스크립트에서 생성하는 샘플 데이터:

```python
# 샘플 거래 기록
TradingHistoryRecord(
    portfolio_id="test_db_check",
    symbol="TEST001",
    order_type="buy", 
    quantity=1.0,
    price=1000.0,
    total_amount=1000.0,
    commission=10.0,
    order_id="TEST_DB_CHECK_001",
    status="completed",
    environment="demo"
)

# 샘플 시스템 로그  
SystemLogRecord(
    level="INFO",
    module="db_test",
    message="DB 연결 테스트 완료",
    environment="demo",
    extra_data={"test_success": True, "tables_checked": 4}
)
```

## kis_debug.py와의 차이점

| 기능 | db_test.py | kis_debug.py |
|------|-----------|--------------|
| KIS API 테스트 | ❌ | ✅ |
| 웹 서버 테스트 | ❌ | ✅ |
| DB 테스트 | ✅ | ✅ |
| 실행 시간 | 빠름 | 보통 |
| 의존성 | 최소 | 많음 |
| 용도 | DB 전용 | 종합 진단 |

## 결론

`db_test.py`는 데이터베이스 상태만을 빠르고 간단하게 확인하고 싶을 때 사용하는 전용 도구입니다. 전체 시스템 진단이 필요한 경우에는 `kis_debug.py`를 사용하고, DB만 확인하고 싶을 때는 이 스크립트를 사용하세요.