# 거래 데이터 DB 저장 문제 해결 가이드

## 문제 상황: 거래는 발생했지만 DB에 데이터가 저장되지 않음

**현상:**
- 모의계좌에서 실제 거래가 발생함 (삼성전자, 네이버, SK하이닉스 매수)
- DB 확인 결과 거래 기록이 0건으로 표시됨

**근본 원인:** 
`portfolio_rebalancing.py`를 `--db-mode` 플래그 없이 실행하여 DB 저장 기능이 비활성화됨

## DB 모드 동작 원리

### 1. 명령줄 플래그 확인
```python
parser.add_argument(
    '--db-mode',
    action='store_true',
    help='Enable database logging and storage'
)

# --db-mode 플래그 없으면 args.db_mode = False
db_enabled = args.db_mode
```

### 2. DB 매니저 초기화 조건
```python
def __init__(self, db_enabled: bool = False):
    self.db_manager = None
    
    # db_enabled가 False이면 DB 매니저가 초기화되지 않음
    if self.db_enabled:
        self.db_manager = DatabaseManager()
    else:
        # DB 매니저는 None으로 유지됨
```

### 3. DB 저장 실행 조건
```python
def run_once(self):
    if result.succeeded:
        # db_manager가 None이면 이 블록은 실행되지 않음
        if self.db_manager:
            self._save_to_database(portfolio_snapshot, plan, result)
```

## DB 모드 동작 확인 방법

### 1. 명령줄 옵션 확인
```bash
python Scripts\apps\portfolio_rebalancing.py --help | Select-String -Pattern "db-mode"
```
출력 예시:
```
--db-mode             Enable database logging and storage
```

### 2. DB 비활성화 상태 확인
```bash
python Scripts\apps\portfolio_rebalancing.py --validate-only --demo 2>&1 | Select-String -Pattern "DB:"
```
출력 예시:
```
Starting Portfolio Rebalancing Application (DB: disabled)
```

### 3. DB 활성화 상태 확인
```bash
python Scripts\apps\portfolio_rebalancing.py --validate-only --demo --db-mode 2>&1 | Select-String -Pattern "DB:|Database"
```
출력 예시:
```
🗄️ Database mode enabled - All trading data will be stored
Starting Portfolio Rebalancing Application (DB: enabled)
```

### 4. 테스트 스크립트로 종합 확인
```bash
python Scripts\temp\test_db_mode_verification.py
```

## 올바른 실행 방법

### DB 모드로 포트폴리오 리밸런싱 실행
```bash
# 한 번 실행 (DB 저장 포함)
python Scripts\apps\portfolio_rebalancing.py --mode once --db-mode

# 스케줄러 실행 (DB 저장 포함)  
python Scripts\apps\portfolio_rebalancing.py --mode schedule --db-mode

# 모의투자 + DB 모드
python Scripts\apps\portfolio_rebalancing.py --demo --db-mode

# 웹 서버 + DB 모드
python Scripts\apps\portfolio_rebalancing.py --db-mode --web-port 5001
```

### DB 모드 활성화 확인 방법
로그에서 다음 메시지 확인:
```
🗄️ Database mode enabled - All trading data will be stored
Database manager initialized and tables created
```
```bash
# 한 번 실행 (DB 저장 포함)
python Scripts\apps\portfolio_rebalancing.py --mode once --db-mode

# 스케줄러 실행 (DB 저장 포함)  
python Scripts\apps\portfolio_rebalancing.py --mode schedule --db-mode

# 모의투자 + DB 모드
python Scripts\apps\portfolio_rebalancing.py --demo --db-mode

# 웹 서버 + DB 모드
python Scripts\apps\portfolio_rebalancing.py --db-mode --web-port 5001
```

### DB 모드 활성화 확인 방법
로그에서 다음 메시지 확인:
```
🗄️ Database mode enabled - All trading data will be stored
Database manager initialized and tables created
```

## DB 저장 로직 분석

### 거래 기록 저장 과정
1. **주문 실행 성공 시**
   ```python
   if result.succeeded:
       logger.info(f"Plan executed successfully: {len(result.executed_orders)} orders")
   ```

2. **DB 저장 실행**
   ```python
   if self.db_manager:
       self._save_to_database(portfolio_snapshot, plan, result)
   ```

3. **실제 저장 로직**
   ```python
   for order in result.executed_orders:
       trading_record = TradingHistoryRecord(
           portfolio_id=portfolio_snapshot.portfolio_id,
           symbol=order.symbol,
           order_type='buy' if order.side == 'buy' else 'sell',
           quantity=float(order.quantity),
           price=float(order.price),
           total_amount=float(order.quantity * order.price),
           order_id=order.order_id,
           status='completed',
           environment=env
       )
       self.db_manager.save_trading_history(trading_record)
   ```

## 문제 진단 체크리스트

### 실행 시 확인사항
- [ ] `--db-mode` 플래그로 실행했는가?
- [ ] 로그에 "Database mode enabled" 메시지가 있는가?
- [ ] PostgreSQL 서버가 실행 중인가?
- [ ] Config\database.json 설정이 올바른가?

### DB 연결 확인
```bash
# 1. DB 테스트 스크립트 실행
python Scripts\tests\db_test.py

# 2. PostgreSQL 프로세스 확인
Get-Process postgres -ErrorAction SilentlyContinue

# 3. 포트 확인  
netstat -an | findstr 5432
```

### 저장 성공 로그 확인
```
Successfully saved N trading records to database
```

## 해결 방안

### 즉시 해결
1. **앞으로 DB 모드로 실행**
   ```bash
   python Scripts\apps\portfolio_rebalancing.py --demo --db-mode
   ```

2. **과거 거래 데이터 수동 입력 (선택사항)**
   ```python
   # Scripts\temp\manual_trade_insert.py 에 스크립트 작성
   # 모의계좌 거래 내역을 수동으로 DB에 삽입
   ```

### 장기 개선
1. **기본값 변경 (옵션)**
   ```python
   # portfolio_rebalancing.py 수정하여 기본값을 True로 변경
   def __init__(self, db_enabled: bool = True):
   ```

2. **실행 스크립트 작성**
   ```bash
   # run_portfolio_with_db.bat
   python Scripts\apps\portfolio_rebalancing.py --demo --db-mode
   ```

## 데이터베이스 요구사항

### 1. PostgreSQL 설치 및 실행
- localhost:5432에서 실행 중이어야 함
- 데이터베이스: appdb
- 사용자: appuser
- 비밀번호: temp1234

### 2. Python 패키지
```bash
pip install psycopg2-binary
```

### 3. 설정 파일
Config\database.json:
```json
{
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "appdb",
        "user": "appuser",
        "password": "temp1234"
    }
}
```

## 결론

**검증 완료:**
✅ `--db-mode` 플래그 없이 실행 시: "DB: disabled" 로그 출력
✅ `--db-mode` 플래그로 실행 시: "DB: enabled" 및 "Database mode enabled" 로그 출력

**문제의 핵심:**
- 거래는 정상적으로 실행되었으나, `--db-mode` 플래그 없이 실행되어 DB 저장 로직이 완전히 건너뛰어짐
- `self.db_manager`가 None이므로 DB 저장 코드가 실행되지 않음

**해결책:**
- 앞으로는 반드시 `--db-mode` 플래그를 포함하여 포트폴리오 리밸런싱을 실행해야 함
- PostgreSQL 서버 실행이 필요하지만, 서버 없이도 플래그 동작은 정상 확인됨

**예방 조치:**
- 실행 스크립트에 `--db-mode` 플래그를 기본 포함
- 로그 모니터링으로 DB 저장 성공 여부 확인

**테스트 결과:**
- 명령줄 옵션: ✅ 정상 동작
- DB 플래그 인식: ✅ 정상 동작 
- 로그 메시지: ✅ 정확한 상태 표시