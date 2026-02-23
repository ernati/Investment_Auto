# DB 테스트 데이터 삽입 스크립트 문서

## 개요

`insert_test_data.py` 스크립트는 Investment_Auto 시스템의 데이터베이스에 현실적인 테스트 데이터를 생성하고 삽입하는 도구입니다. 
웹 인터페이스의 DB 데이터 시각화 기능을 테스트하고 시연하기 위한 목적으로 사용됩니다.  

## 주요 기능

### 1. 거래 기록 생성 (Trading History)
- **총 15건의 거래 데이터** 생성
- 최근 7일간의 랜덤 거래 시간 분산
- 실제 종목 코드와 가격 범위 사용
- 다양한 주문 유형과 상태 포함

### 2. 리밸런싱 로그 생성 (Rebalancing Logs)  
- **3건의 리밸런싱 시나리오** 생성
- 정기 리밸런싱, 임계치 초과, 시장 급락 대응 등
- 실제 비중 변화와 실행 결과 포함
- 성공/실패/부분성공 상태 시뮬레이션

### 3. 포트폴리오 스냅샷 생성 (Portfolio Snapshots)
- **10일간의 일일 스냅샷** 생성
- 시간에 따른 자산 가치 변동 시뮬레이션  
- 4개 주요 포지션 (삼성전자, 네이버, SK하이닉스, 현금)
- 랜덤 가격 변동과 비중 변화

### 4. 시스템 로그 생성 (System Logs)
- **10건의 시스템 로그** 생성 
- 다양한 모듈과 로그 레벨 포함
- INFO/WARNING/ERROR 레벨 분산
- 실제 시스템 메시지와 추가 데이터

## 생성되는 테스트 데이터

### 거래 기록 (Trading History)

#### 지원 종목
| 종목코드 | 종목명 | 가격 범위 |
|----------|--------|-----------|
| 005930 | 삼성전자 | 70,000 ~ 80,000원 |
| 035420 | NAVER | 200,000 ~ 250,000원 |  
| 000660 | SK하이닉스 | 80,000 ~ 120,000원 |
| KRW | 현금 | 1원 (고정) |

#### 거래 특성
- **거래량**: 10/50/100/200주 (주식), 100만~500만원 (현금)
- **주문 유형**: buy, sell, deposit
- **수수료**: 거래금액의 0.2% (주식만)
- **성공률**: 80% 완료, 10% 실패, 10% 대기
- **거래시간**: 영업일 오전 9시 ~ 오후 3시

### 리밸런싱 로그 (Rebalancing Logs)

#### 시나리오 1: 정기 리밸런싱
- **사유**: "정기 리밸런싱 - 월간 스케줄"
- **목표 비중**: 삼성전자 50%, 네이버 30%, 현금 20%
- **실행 주문**: 3건
- **상태**: 성공

#### 시나리오 2: 임계치 초과
- **사유**: "임계치 초과 리밸런싱 - 삼성전자 비중 과다"  
- **목표 비중**: 삼성전자 40%, 네이버 30%, SK하이닉스 20%, 현금 10%
- **실행 주문**: 5건
- **상태**: 성공

#### 시나리오 3: 시장 급락 대응
- **사유**: "시장 급락 대응 리밸런싱"
- **목표 비중**: 삼성전자 30%, 네이버 20%, SK하이닉스 20%, 현금 30% 
- **실행 주문**: 4건
- **상태**: 부분성공 (일부 주문 체결 지연)

1. **DB 연결 확인**: PostgreSQL 서버 실행 및 연결 상태 확인
2. **테스트 데이터 삽입**: 각 테이블에 샘플 데이터 생성
3. **데이터 검증**: `db_test.py` 실행으로 삽입된 데이터 확인

```bash
# 1단계: 테스트 데이터 삽입
python Scripts/tests/insert_test_data.py

# 2단계: 삽입된 데이터 확인  
python Scripts/tests/db_test.py
```

## 실행 결과 예시

### 성공적인 실행
```
🌱 DB 테스트 데이터 삽입 시작
============================================================
📡 데이터베이스 연결 중...
✅ 데이터베이스 연결 성공

📈 거래 기록 샘플 데이터 생성...
  ✅ 1/15: 삼성전자 buy 100주 @ 75,000원
  ✅ 2/15: NAVER sell 50주 @ 230,000원
  ✅ 3/15: 현금 deposit 2,000,000주 @ 1원
  ...
  📊 거래 기록 생성 완료: 15/15건 성공

⚖️ 리밸런싱 로그 샘플 데이터 생성...
  ✅ 1: success | 3건 실행 | 정기 리밸런싱 - 월간 스케줄...
  ✅ 2: success | 5건 실행 | 임계치 초과 리밸런싱 - 삼성전자...
  ✅ 3: partial | 4건 실행 | 시장 급락 대응 리밸런싱...
  📊 리밸런싱 로그 생성 완료: 3/3건 성공

📸 포트폴리오 스냅샷 샘플 데이터 생성...
  ✅ Day 1: 총자산 14,850,000원 | 포지션 4개
  ✅ Day 2: 총자산 15,120,000원 | 포지션 4개
  ...
  📊 포트폴리오 스냅샷 생성 완료: 10/10건 성공

📋 시스템 로그 샘플 데이터 생성...
  ✅ 1: INFO | kis_auth | KIS API 인증 성공...
  ✅ 2: INFO | portfolio_fetcher | 포트폴리오 데이터 조회 완료...
  ✅ 3: WARNING | kis_trading | 주문 체결 지연 발생...
  ...
  📊 시스템 로그 생성 완료: 10/10건 성공

📊 테스트 데이터 삽입 결과:
  ✅ 성공 trading_history
  ✅ 성공 rebalancing_logs  
  ✅ 성공 portfolio_snapshots
  ✅ 성공 system_logs

🎯 총 4/4개 테이블에 데이터 삽입 완료

✅ 모든 테스트 데이터 삽입 완료!
💡 이제 db_test.py를 실행하여 데이터가 제대로 읽히는지 확인하세요.
```

## 생성되는 테스트 데이터 상세

### 거래 기록 (trading_history)

```python
# 예시 거래 기록
- 삼성전자 매수: 100주 @ 75,000원, 수수료 150원
- NAVER 매도: 50주 @ 230,000원, 수수료 230원  
- 현금 입금: 2,000,000원, 수수료 0원
- 상태: completed(80%), failed(10%), pending(10%)
```

### 리밸런싱 로그 (rebalancing_logs)

```python
# 시나리오 1: 정기 리밸런싱
{
    "reason": "정기 리밸런싱 - 월간 스케줄",
    "target_weights": {"005930": 0.5, "035420": 0.3, "KRW": 0.2},
    "before_weights": {"005930": 0.45, "035420": 0.35, "KRW": 0.2},
    "after_weights": {"005930": 0.5, "035420": 0.3, "KRW": 0.2},
    "status": "success",
    "orders_executed": 3
}
```

### 포트폴리오 스냅샷 (portfolio_snapshots)

```python
# 예시 포지션 데이터
{
    "005930": {
        "symbol": "005930",
        "name": "삼성전자", 
        "quantity": 100,
        "current_price": 75000,
        "market_value": 7500000,
        "weight": 0.50
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

### 시스템 로그 (system_logs)

```python
# 다양한 로그 레벨과 모듈
- INFO: KIS API 인증 성공, 포트폴리오 조회 완료
- WARNING: 주문 체결 지연, 시장 종료 시간 접근  
- ERROR: API Rate limit 초과, 주문 실행 실패
```

## 활용 시나리오

### 1. 개발 환경 준비
```bash
# 새 개발 환경에서 DB 설정 후 테스트 데이터 준비
python Scripts/tests/insert_test_data.py
```

### 2. 기능 테스트 준비  
```bash
# 새로운 데이터 조회/분석 기능 개발 전 준비
python Scripts/tests/insert_test_data.py
python Scripts/tests/db_test.py
```

### 3. 데모 환경 구축
```bash
# 클라이언트 데모나 발표용 데이터 준비
python Scripts/tests/insert_test_data.py
```

### 4. 문제 재현
```bash
# 버그 재현이나 디버깅을 위한 일관된 테스트 환경 조성
python Scripts/tests/insert_test_data.py
```

## 데이터 특징

### 현실적인 시나리오
- **거래 시간**: 영업일 9-15시 집중
- **가격 변동**: 실제 주식 가격대 반영
- **수수료**: 0.2% 거래 수수료 적용
- **비중 변화**: 자연스러운 포트폴리오 비중 이동

### 다양한 상태
- **성공/실패**: 대부분 성공, 일부 실패 케이스 포함
- **부분 체결**: 리밸런싱에서 부분 실패 시나리오
- **다양한 로그**: INFO/WARNING/ERROR 로그 분산

### 시계열 데이터
- **최근성**: 최근 7-10일 데이터로 현재와 연관성 유지
- **연속성**: 포트폴리오 가치의 자연스러운 변동
- **패턴**: 실제 거래 패턴과 유사한 데이터 분포

## 주의사항

### 1. demo 환경 전용
- 모든 데이터는 `environment="demo"`로 생성
- 실제 거래 데이터와 구분되어 안전

### 2. 중복 실행
- 스크립트를 여러 번 실행하면 데이터가 누적됨
- 필요시 테이블 정리 후 재실행 권장

### 3. DB 연결 필수
- PostgreSQL 서버가 실행되어 있어야 함
- database.json 설정이 올바르게 되어 있어야 함

## 에러 처리

### DB 연결 실패
```bash
❌ 데이터베이스 초기화 실패
💡 확인사항:
   - PostgreSQL 서비스가 실행 중인가요?
   - Config/database.json 설정이 올바른가요?
```

### 부분 실패
```bash
⚠️ 일부 테이블에 데이터 삽입 실패
  ✅ 성공 trading_history
  ❌ 실패 rebalancing_logs
```

## 관련 파일

- **실행**: `Scripts/tests/insert_test_data.py`
- **검증**: `Scripts/tests/db_test.py`
- **설정**: `Config/database.json`
- **모델**: `Scripts/modules/db_models.py`
- **DB 관리**: `Scripts/modules/db_manager.py`

## 문제 해결

### 권한 오류
```sql
-- PostgreSQL에서 권한 부여
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO appuser;
```

### 데이터 정리
```sql
-- 테스트 데이터 정리 (필요시)
DELETE FROM trading_history WHERE environment = 'demo';
DELETE FROM rebalancing_logs WHERE environment = 'demo'; 
DELETE FROM portfolio_snapshots WHERE environment = 'demo';
DELETE FROM system_logs WHERE environment = 'demo';
```

### 스키마 초기화
```bash
# DatabaseManager가 자동으로 테이블 생성
python -c "from Scripts.modules.db_manager import DatabaseManager; DatabaseManager()"
```

## 결론

`insert_test_data.py`는 개발과 테스트에 필요한 현실적인 데이터를 제공하는 중요한 도구입니다. `db_test.py`와 함께 사용하여 데이터베이스 기능의 완전한 검증 환경을 구축할 수 있습니다.