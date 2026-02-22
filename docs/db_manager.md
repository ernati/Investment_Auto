# DatabaseManager 모듈 문서

## 개요

`db_manager.py` 모듈은 Investment_Auto 시스템의 데이터베이스 연결 및 관리를 담당하는 핵심 모듈입니다.
PostgreSQL 데이터베이스와의 연결을 관리하고, 거래 기록, 리밸런싱 로그, 포트폴리오 스냅샷, 시스템 로그 등을 저장/조회하는 기능을 제공합니다.

## 주요 기능

- **데이터베이스 연결 관리**: 자동 재연결 및 연결 풀링
- **테이블 자동 생성**: 필요한 모든 테이블을 자동으로 생성
- **데이터 저장/조회**: 거래 내역, 리밸런싱 로그 등의 CRUD 작업
- **데이터 정리**: 보존 기간에 따른 오래된 데이터 자동 정리
- **에러 핸들링**: 연결 실패 시 자동 재시도 및 로깅

## 설정 파일

설정 파일은 `Config/database.json`에 위치하며, 다음과 같은 구조를 가집니다:

```json
{
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "investment_auto", 
        "user": "investment_user",
        "password": "your_password_here",
        "sslmode": "prefer",
        "connect_timeout": 5,
        "retry_max": 3,
        "retry_backoff": 0.5
    },
    "table_config": {
        "trading_history": {
            "enabled": true,
            "retention_days": 365
        },
        "rebalancing_logs": {
            "enabled": true,
            "retention_days": 365
        },
        "portfolio_snapshots": {
            "enabled": true,
            "retention_days": 90
        },
        "system_logs": {
            "enabled": true,
            "retention_days": 30
        }
    },
    "logging": {
        "level": "INFO",
        "enable_query_log": false,
        "max_query_length": 1000
    }
}
```

## 클래스 및 메서드

### DatabaseManager 클래스

#### 초기화

```python
from modules.db_manager import DatabaseManager

# 기본 설정으로 초기화
db_manager = DatabaseManager()

# 사용자 정의 설정 파일로 초기화
db_manager = DatabaseManager("/path/to/custom/database.json")
```

#### 주요 메서드

##### 연결 관리

- `test_connection()`: 데이터베이스 연결 테스트
- `create_tables()`: 모든 테이블 생성
- `get_connection()`: 컨텍스트 매니저로 안전한 연결 관리

##### 데이터 저장

- `save_trading_history(record: TradingHistoryRecord)`: 거래 기록 저장
- `save_rebalancing_log(record: RebalancingLogRecord)`: 리밸런싱 로그 저장
- `save_portfolio_snapshot(record: PortfolioSnapshotRecord)`: 포트폴리오 스냅샷 저장
- `save_system_log(record: SystemLogRecord)`: 시스템 로그 저장

##### 데이터 조회

- `get_trading_history(portfolio_id, environment, limit=100, offset=0)`: 거래 기록 조회
- `get_rebalancing_logs(portfolio_id, environment, limit=50, offset=0)`: 리밸런싱 로그 조회
- `get_portfolio_snapshots(portfolio_id, environment, limit=30, offset=0)`: 포트폴리오 스냅샷 조회

##### 유지보수

- `cleanup_old_data(environment)`: 오래된 데이터 정리

## 사용 예시

### 1. 기본 설정 및 연결 테스트

```python
from modules.db_manager import DatabaseManager

# 데이터베이스 매니저 초기화
db_manager = DatabaseManager()

# 연결 테스트
if db_manager.test_connection():
    print("데이터베이스 연결 성공")
    
    # 테이블 생성
    if db_manager.create_tables():
        print("테이블 생성 완료")
else:
    print("데이터베이스 연결 실패")
```

### 2. 거래 기록 저장

```python
from modules.db_models import TradingHistoryRecord

# 거래 기록 생성
record = TradingHistoryRecord(
    portfolio_id="portfolio_001",
    symbol="005930",  # 삼성전자
    order_type="buy",
    quantity=10.0,
    price=75000.0,
    total_amount=750000.0,
    commission=1500.0,
    order_id="ORD_001",
    status="completed",
    environment="demo"
)

# 데이터베이스에 저장
if db_manager.save_trading_history(record):
    print("거래 기록 저장 완료")
```

### 3. 데이터 조회

```python
# 거래 기록 조회
trading_history = db_manager.get_trading_history(
    portfolio_id="portfolio_001",
    environment="demo",
    limit=50
)

for trade in trading_history:
    print(f"{trade['timestamp']}: {trade['symbol']} {trade['order_type']} "
          f"{trade['quantity']}주 @ {trade['price']}원")
```

### 4. 리밸런싱 로그 저장

```python
from modules.db_models import RebalancingLogRecord

rebalancing_record = RebalancingLogRecord(
    portfolio_id="portfolio_001",
    rebalance_reason="Scheduled rebalancing",
    target_weights={"005930": 0.5, "035420": 0.3, "KRW": 0.2},
    before_weights={"005930": 0.4, "035420": 0.4, "KRW": 0.2},
    after_weights={"005930": 0.5, "035420": 0.3, "KRW": 0.2},
    orders_executed=2,
    status="success",
    environment="demo"
)

db_manager.save_rebalancing_log(rebalancing_record)
```

## 의존성

- `psycopg2` 또는 `psycopg2-binary`: PostgreSQL 연결
- `json`: 설정 파일 파싱
- `logging`: 로깅
- `datetime`: 시간 관련 작업

## 설치 요구사항

```bash
pip install psycopg2-binary
```

## 테이블 구조

DatabaseManager가 자동으로 생성하는 테이블들:

1. **trading_history**: 모든 거래 기록
2. **rebalancing_logs**: 리밸런싱 실행 로그
3. **portfolio_snapshots**: 일정 시점의 포트폴리오 상태
4. **system_logs**: 시스템 로그 및 에러 기록

각 테이블의 상세 구조는 `db_models.md` 문서를 참조하세요.

## 주의사항

1. **보안**: 데이터베이스 비밀번호는 환경 변수나 안전한 설정 파일에 저장하세요
2. **연결 관리**: `get_connection()` 컨텍스트 매니저를 사용하여 안전한 연결 관리를 하세요
3. **에러 처리**: 모든 DB 작업은 try-catch 블록으로 감싸여 있으며, 실패 시 로그에 기록됩니다
4. **성능**: 대용량 데이터 조회 시 limit과 offset을 적절히 사용하세요

## 문제 해결

### 연결 오류
- PostgreSQL 서비스가 실행 중인지 확인
- 방화벽 설정 확인
- 사용자 권한 확인

### 권한 오류
- PostgreSQL 사용자에게 데이터베이스 생성/수정 권한이 있는지 확인
- 테이블 스키마 권한 확인

### 성능 문제
- 데이터베이스 인덱스 확인
- 쿼리 실행 계획 분석
- 연결 풀 설정 조정