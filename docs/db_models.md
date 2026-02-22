# Database Models 모듈 문서

## 개요

`db_models.py` 모듈은 Investment_Auto 시스템에서 사용하는 데이터베이스 테이블 스키마와 데이터 모델을 정의합니다.
Python 데이터클래스를 사용하여 타입 안전성을 보장하고, SQL 테이블 생성 스크립트를 포함합니다.

## 데이터 모델

### 1. TradingHistoryRecord

거래 기록을 저장하는 모델입니다.

#### 필드

| 필드명 | 타입 | 설명 | 필수 |
|--------|------|------|------|
| `portfolio_id` | str | 포트폴리오 식별자 | ✓ |
| `symbol` | str | 종목 코드 (예: "005930", "KRW") | ✓ |
| `order_type` | str | 주문 유형 ("buy", "sell") | ✓ |
| `quantity` | float | 거래 수량 | ✓ |
| `price` | float | 거래 가격 | ✓ |
| `total_amount` | float | 총 거래 금액 | ✓ |
| `commission` | float | 수수료 | ✓ |
| `order_id` | str | 주문 식별자 | ✓ |
| `status` | str | 주문 상태 ("completed", "failed", "pending") | ✓ |
| `environment` | str | 환경 ("real", "demo") | ✓ |
| `timestamp` | datetime | 거래 시각 (자동 설정) | - |
| `id` | int | 기본 키 (자동 증가) | - |

#### 사용 예시

```python
from modules.db_models import TradingHistoryRecord

record = TradingHistoryRecord(
    portfolio_id="portfolio_001",
    symbol="005930",
    order_type="buy",
    quantity=10.0,
    price=75000.0,
    total_amount=750000.0,
    commission=1500.0,
    order_id="ORD_20260221_001",
    status="completed",
    environment="demo"
)

# JSON으로 변환
json_data = record.to_dict()
```

### 2. RebalancingLogRecord

리밸런싱 실행 로그를 저장하는 모델입니다.

#### 필드

| 필드명 | 타입 | 설명 | 필수 |
|--------|------|------|------|
| `portfolio_id` | str | 포트폴리오 식별자 | ✓ |
| `rebalance_reason` | str | 리밸런싱 사유 | ✓ |
| `target_weights` | Dict[str, Any] | 목표 비중 | ✓ |
| `before_weights` | Dict[str, Any] | 리밸런싱 전 비중 | ✓ |
| `after_weights` | Dict[str, Any] | 리밸런싱 후 비중 | ✓ |
| `orders_executed` | int | 실행된 주문 수 | ✓ |
| `status` | str | 실행 상태 ("success", "failed", "partial") | ✓ |
| `environment` | str | 환경 ("real", "demo") | ✓ |
| `error_message` | str | 오류 메시지 (실패 시) | - |
| `timestamp` | datetime | 실행 시각 (자동 설정) | - |
| `id` | int | 기본 키 (자동 증가) | - |

#### 사용 예시

```python
from modules.db_models import RebalancingLogRecord

record = RebalancingLogRecord(
    portfolio_id="portfolio_001",
    rebalance_reason="Scheduled rebalancing - deviation threshold exceeded",
    target_weights={
        "005930": 0.50,  # 삼성전자 50%
        "035420": 0.30,  # 네이버 30%
        "KRW": 0.20      # 현금 20%
    },
    before_weights={
        "005930": 0.45,
        "035420": 0.35,
        "KRW": 0.20
    },
    after_weights={
        "005930": 0.50,
        "035420": 0.30,
        "KRW": 0.20
    },
    orders_executed=2,
    status="success",
    environment="demo"
)
```

### 3. PortfolioSnapshotRecord

특정 시점의 포트폴리오 상태를 저장하는 모델입니다.

#### 필드

| 필드명 | 타입 | 설명 | 필수 |
|--------|------|------|------|
| `portfolio_id` | str | 포트폴리오 식별자 | ✓ |
| `total_value` | float | 총 평가 금액 | ✓ |
| `positions` | Dict[str, Any] | 포지션 상세 정보 | ✓ |
| `environment` | str | 환경 ("real", "demo") | ✓ |
| `timestamp` | datetime | 스냅샷 시각 (자동 설정) | - |
| `id` | int | 기본 키 (자동 증가) | - |

#### positions 필드 구조

```json
{
    "005930": {
        "symbol": "005930",
        "name": "삼성전자",
        "quantity": 100,
        "current_price": 75000,
        "market_value": 7500000,
        "weight": 0.50
    },
    "035420": {
        "symbol": "035420", 
        "name": "NAVER",
        "quantity": 20,
        "current_price": 225000,
        "market_value": 4500000,
        "weight": 0.30
    },
    "KRW": {
        "symbol": "KRW",
        "name": "현금",
        "quantity": 3000000,
        "current_price": 1,
        "market_value": 3000000,
        "weight": 0.20
    }
}
```

### 4. SystemLogRecord

시스템 로그를 저장하는 모델입니다.

#### 필드

| 필드명 | 타입 | 설명 | 필수 |
|--------|------|------|------|
| `level` | str | 로그 레벨 ("INFO", "ERROR", "WARNING") | ✓ |
| `module` | str | 모듈명 | ✓ |
| `message` | str | 로그 메시지 | ✓ |
| `environment` | str | 환경 ("real", "demo") | ✓ |
| `extra_data` | Dict[str, Any] | 추가 데이터 (JSON) | - |
| `timestamp` | datetime | 로그 시각 (자동 설정) | - |
| `id` | int | 기본 키 (자동 증가) | - |

## 테이블 스키마

### trading_history 테이블

```sql
CREATE TABLE IF NOT EXISTS trading_history (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    portfolio_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(10) NOT NULL,
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    commission DECIMAL(15,2) DEFAULT 0,
    order_id VARCHAR(100),
    status VARCHAR(20) NOT NULL,
    environment VARCHAR(10) NOT NULL,
    
    INDEX idx_trading_timestamp (timestamp),
    INDEX idx_trading_portfolio (portfolio_id),
    INDEX idx_trading_symbol (symbol),
    INDEX idx_trading_environment (environment)
);
```

### rebalancing_logs 테이블

```sql
CREATE TABLE IF NOT EXISTS rebalancing_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    portfolio_id VARCHAR(50) NOT NULL,
    rebalance_reason TEXT NOT NULL,
    target_weights JSON NOT NULL,
    before_weights JSON NOT NULL,
    after_weights JSON NOT NULL,
    orders_executed INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    environment VARCHAR(10) NOT NULL,
    
    INDEX idx_rebalancing_timestamp (timestamp),
    INDEX idx_rebalancing_portfolio (portfolio_id),
    INDEX idx_rebalancing_status (status),
    INDEX idx_rebalancing_environment (environment)
);
```

### portfolio_snapshots 테이블

```sql
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    portfolio_id VARCHAR(50) NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    positions JSON NOT NULL,
    environment VARCHAR(10) NOT NULL,
    
    INDEX idx_snapshot_timestamp (timestamp),
    INDEX idx_snapshot_portfolio (portfolio_id),
    INDEX idx_snapshot_environment (environment)
);
```

### system_logs 테이블

```sql
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20) NOT NULL,
    module VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    extra_data JSON,
    environment VARCHAR(10) NOT NULL,
    
    INDEX idx_system_timestamp (timestamp),
    INDEX idx_system_level (level),
    INDEX idx_system_module (module),
    INDEX idx_system_environment (environment)
);
```

## 데이터 정리 정책

각 테이블은 설정된 보존 기간에 따라 자동으로 정리됩니다:

- `trading_history`: 365일 (1년)
- `rebalancing_logs`: 365일 (1년)  
- `portfolio_snapshots`: 90일 (3개월)
- `system_logs`: 30일 (1개월)

보존 기간은 `Config/database.json` 파일에서 조정할 수 있습니다.

## 인덱스 전략

성능 최적화를 위해 다음 인덱스가 생성됩니다:

### 공통 인덱스
- `timestamp`: 시간 기반 조회 최적화
- `environment`: 환경별 분리 조회
- `portfolio_id`: 포트폴리오별 조회

### 테이블별 특수 인덱스
- `trading_history`: `symbol` (종목별 조회)
- `rebalancing_logs`: `status` (상태별 조회)
- `system_logs`: `level`, `module` (로그 레벨/모듈별 조회)

## 사용 시 고려사항

### 1. 데이터 타입

- **금액**: `DECIMAL(15,2)` 사용하여 정확한 소수점 계산
- **수량**: `DECIMAL(15,8)` 사용하여 소수점 이하 수량 지원
- **JSON**: PostgreSQL의 네이티브 JSON 타입 활용

### 2. 성능

- **대용량 조회**: `LIMIT`과 `OFFSET`을 사용한 페이지네이션
- **시간 범위 조회**: `timestamp` 인덱스 활용
- **복잡한 JSON 쿼리**: PostgreSQL의 JSON 연산자 활용

### 3. 확장성

- **파티션**: 시간 기반 테이블 파티셔닝 고려
- **아카이브**: 오래된 데이터의 별도 아카이브 테이블 고려
- **읽기 복제본**: 조회 트래픽 분산을 위한 읽기 전용 복제본 고려

## 마이그레이션

스키마 변경 시 고려사항:

1. **백워드 호환성**: 기존 데이터 유지
2. **인덱스 재생성**: 스키마 변경 후 인덱스 최적화
3. **데이터 검증**: 마이그레이션 후 데이터 무결성 확인

## 관련 모듈

- `db_manager.py`: 데이터베이스 연결 및 CRUD 작업
- `portfolio_rebalancing.py`: 메인 애플리케이션에서 DB 모드 지원
- `config_loader.py`: 설정 관리