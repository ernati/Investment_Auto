# DB 모드 체크 리포트

## 개요

`portfolio_rebalancing.py` 애플리케이션의 `--db-mode` 옵션 동작과 관련된 코드 분석 결과입니다.

---

## 1. --db-mode 옵션 동작 흐름

### ✅ 정상 작동 확인

```
portfolio_rebalancing.py (main 함수)
  │
  ├─ argparse로 --db-mode 옵션 파싱
  │
  ├─ db_enabled = args.db_mode
  │
  └─ PortfolioRebalancingApp 생성자
       │
       ├─ DB_AVAILABLE 체크 (psycopg2 import 가능 여부)
       │
       ├─ db_enabled=True 일 때 DatabaseManager 초기화
       │
       └─ run_once() 실행 시 거래 성공 → _save_to_database() 호출
```

### 명령어 사용법

```bash
# DB 모드 활성화
python Scripts/apps/portfolio_rebalancing.py --db-mode --demo

# DB 모드 + 웹 서버 + 스케줄러
python Scripts/apps/portfolio_rebalancing.py --db-mode --mode schedule --demo
```

---

## 2. 거래 시 DB 저장 흐름

### ✅ 저장되는 데이터 종류

| 테이블 | 레코드 클래스 | 저장 시점 |
|--------|--------------|-----------|
| `trading_history` | `TradingHistoryRecord` | 각 주문 실행 완료 후 |
| `rebalancing_logs` | `RebalancingLogRecord` | 리밸런싱 완료/실패 후 |
| `portfolio_snapshots` | `PortfolioSnapshotRecord` | 거래 전 포트폴리오 상태 |
| `system_logs` | `SystemLogRecord` | 시스템 이벤트 발생 시 |

### 저장 흐름

```python
# portfolio_rebalancing.py > run_once()
def run_once(self):
    # 1. 포트폴리오 스냅샷 생성
    portfolio_snapshot = self.portfolio_fetcher.fetch_portfolio_snapshot(...)
    
    # 2. 리밸런싱 계획 생성 및 실행
    result = self.order_executor.execute_plan(adjusted_plan)
    
    # 3. DB 저장 (db_enabled=True일 때만)
    if self.db_manager:
        self._save_to_database(portfolio_snapshot, adjusted_plan, result)
```

---

## 3. Web에서 DB 조회

### ✅ 제공되는 API 엔드포인트

| 엔드포인트 | 설명 | 필터 파라미터 |
|-----------|------|--------------|
| `/api/db/trading-history` | 거래 기록 조회 | portfolio_id, environment, limit, offset |
| `/api/db/rebalancing-logs` | 리밸런싱 로그 조회 | portfolio_id, environment, limit, offset |
| `/api/db/portfolio-snapshots` | 포트폴리오 스냅샷 조회 | portfolio_id, environment, limit, offset |
| `/api/db/system-logs` | 시스템 로그 조회 | level, module, environment, limit, offset |
| `/health` | 헬스 체크 (DB 상태 포함) | - |

### Web UI 접근 방법

```bash
# 웹 서버 시작 (DB 연동)
python Scripts/apps/portfolio_web_app.py --port 5000 --env demo
```

**접속 URL**: http://127.0.0.1:5000

**UI 구성**:
- 📊 실시간 대시보드: 포트폴리오 현황
- 🗄️ 데이터베이스: DB 저장 데이터 조회

---

## 4. 발견된 문제점 및 수정 내역

### 🔧 수정 완료

#### 문제 1: portfolio_id 불일치
- **원인**: config_basic.json에서는 `portfolio-001` 사용, 웹 UI에서는 `demo_portfolio` 기본값 사용
- **영향**: 웹에서 DB 조회 시 데이터가 표시되지 않음
- **수정**: portfolio.html의 기본값을 `portfolio-001`로 변경

#### 문제 2: positions 직렬화 안전성
- **원인**: `portfolio_snapshot.positions`가 dict가 아닐 경우 `json.dumps()` 실패 가능
- **수정**: `_save_to_database()`에서 positions 데이터 타입 체크 추가

#### 문제 3: plan 속성 접근 안전성
- **원인**: `plan.target_weights` 등 속성이 없을 경우 에러 발생 가능
- **수정**: `_save_rebalancing_log()`에서 `getattr()` 사용 및 타입 체크 추가

---

## 5. 수정된 파일

| 파일 | 수정 내용 |
|------|----------|
| `Scripts/apps/portfolio_rebalancing.py` | `_save_to_database()`, `_save_rebalancing_log()` 안전성 향상 |
| `Scripts/templates/portfolio.html` | portfolio_id 기본값 수정 (`demo_portfolio` → `portfolio-001`) |
| `Scripts/tests/kis_debug.py` | 테스트 함수의 portfolio_id 수정 |

---

## 6. DB 테이블 스키마

### trading_history
```sql
CREATE TABLE IF NOT EXISTS trading_history (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    portfolio_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    order_type VARCHAR(10) NOT NULL,  -- 'buy', 'sell'
    quantity DECIMAL(15,8) NOT NULL,
    price DECIMAL(15,2) NOT NULL,
    total_amount DECIMAL(15,2) NOT NULL,
    commission DECIMAL(15,2) DEFAULT 0,
    order_id VARCHAR(100),
    status VARCHAR(20) NOT NULL,  -- 'completed', 'failed', 'pending'
    environment VARCHAR(10) NOT NULL  -- 'real', 'demo'
);
```

### rebalancing_logs
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
    status VARCHAR(20) NOT NULL,  -- 'success', 'failed', 'partial'
    error_message TEXT,
    environment VARCHAR(10) NOT NULL
);
```

### portfolio_snapshots
```sql
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    portfolio_id VARCHAR(50) NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    positions JSON NOT NULL,
    environment VARCHAR(10) NOT NULL
);
```

### system_logs
```sql
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20) NOT NULL,  -- 'INFO', 'ERROR', 'WARNING'
    module VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    extra_data JSON,
    environment VARCHAR(10) NOT NULL
);
```

---

## 7. 설정 파일

### Config/database.json
```json
{
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "appdb",
        "user": "appuser", 
        "password": "temp1234",
        "sslmode": "prefer",
        "connect_timeout": 5,
        "retry_max": 3,
        "retry_backoff": 0.5
    },
    "table_config": {
        "trading_history": { "enabled": true, "retention_days": 365 },
        "rebalancing_logs": { "enabled": true, "retention_days": 365 },
        "portfolio_snapshots": { "enabled": true, "retention_days": 90 },
        "system_logs": { "enabled": true, "retention_days": 30 }
    }
}
```

---

## 8. 테스트 방법

```bash
# 1. PostgreSQL 서버 실행 확인
# Windows: Get-Service -Name "*postgres*"

# 2. DB 연결 테스트
python Scripts/tests/kis_debug.py

# 3. DB 모드로 리밸런싱 실행
python Scripts/apps/portfolio_rebalancing.py --db-mode --demo --skip-schedule-check

# 4. 웹 서버로 DB 데이터 확인
python Scripts/apps/portfolio_web_app.py --port 5000 --env demo
# 브라우저에서 http://127.0.0.1:5000 접속 → 데이터베이스 탭 확인
```

---

## 9. 결론

| 항목 | 상태 |
|------|------|
| `--db-mode` 옵션 동작 | ✅ 정상 |
| 거래 시 DB 저장 | ✅ 정상 (수정 완료) |
| 웹에서 DB 조회 | ✅ 정상 (portfolio_id 수정 완료) |

**코드 수준에서 DB 모드가 정상적으로 구현되어 있습니다.**  
실제 테스트를 위해서는 PostgreSQL 서버가 실행되어 있어야 합니다.
