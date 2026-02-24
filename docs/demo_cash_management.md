# 모의투자 가상 현금 관리 기능

## 개요

Investment_Auto 프로젝트에 모의투자 환경에서 가상 현금 잔액을 관리하는 기능을 추가했습니다. 이 기능을 통해 모의투자에서도 실제 거래와 유사한 현금 관리 경험을 할 수 있습니다.

## 새로 추가된 파일들

### 1. `modules/demo_cash_manager.py`
모의투자용 가상 현금 관리 핵심 모듈
- JSON 파일 기반 현금 잔액 저장
- 매수/매도 시 현금 차감/증가
- 거래 내역 추적
- 현금 부족 검증

### 2. `test_demo_cash.py`
가상 현금 관리 기능 테스트 스크립트
- 단독 기능 테스트
- 통합 테스트 시뮬레이션
- 현금 부족 시나리오 테스트

### 3. `apps/demo_cash_app.py`
사용자 친화적인 데모 애플리케이션
- 명령줄 인터페이스 제공
- 계좌 잔액 조회
- 가상 매수/매도 주문
- 거래 내역 확인

## 수정된 파일들

### 1. `modules/kis_portfolio_fetcher.py`
- 모의투자 환경에서 가상 현금 관리자를 통한 잔액 조회
- 실전 환경에서는 기존 API 사용

### 2. `modules/kis_trading.py`
- 모의투자 환경에서 주문 성공 시 현금 잔액 자동 업데이트
- 매수 시 현금 차감, 매도 시 현금 증가

## 주요 기능

### 🏛️ 가상 현금 관리
- **초기 잔액**: 계좌당 1,000만원으로 시작
- **현금 추적**: 매수/매도 시 실시간 잔액 업데이트
- **부족 검증**: 현금 부족 시 거래 차단
- **거래 기록**: 모든 거래 내역 JSON 파일에 저장

### 📊 잔액 조회
```python
from modules.demo_cash_manager import get_demo_cash_manager

manager = get_demo_cash_manager("12345678")
balance = manager.get_cash_balance()
print(f"현재 잔액: {balance:,}원")
```

### 📈 매수/매도 시뮬레이션
```python
# 매수 (현금 차감)
success = manager.buy_stock("005930", 10, 75000)  # 삼성전자 10주

# 매도 (현금 증가)  
success = manager.sell_stock("005930", 5, 76000)  # 삼성전자 5주
```

### 📋 거래 내역 조회
```python
history = manager.get_transaction_history(10)  # 최근 10건
for tx in history:
    print(f"{tx['type']}: {tx['amount']:+,}원 (잔액: {tx['balance_after']:,}원)")
```

## 사용법

### 1. 테스트 실행
```bash
cd Scripts
python test_demo_cash.py
```

### 2. 데모 앱 사용
```bash
cd Scripts

# 계좌 잔액 조회
python apps/demo_cash_app.py --action balance

# 매수 시뮬레이션 (삼성전자 10주 @ 75,000원)
python apps/demo_cash_app.py --action buy --stock 005930 --quantity 10 --price 75000

# 매도 시뮬레이션 (삼성전자 5주 @ 76,000원)
python apps/demo_cash_app.py --action sell --stock 005930 --quantity 5 --price 76000

# 거래 내역 조회
python apps/demo_cash_app.py --action history

# 계좌 초기화 (1,000만원)
python apps/demo_cash_app.py --action reset
```

### 3. 기존 코드에서 사용
```python
# 기존 방식 - 모의투자에서 현금 관리 자동 적용
from kis_app_utils import setup_kis_trading_client

# 모의투자 클라이언트 설정
api_client, trading, kis_config = setup_kis_trading_client('demo')

# 계좌 잔액 조회 (가상 현금 관리자 사용)
portfolio_fetcher = KISPortfolioFetcher(api_client.auth)
balance = portfolio_fetcher.fetch_account_balance()
print(f"현금 잔액: {balance['cash']:,}원")

# 매수 주문 (성공 시 자동으로 현금 차감)
result = trading.buy_market_order("005930", 10)
if result['success']:
    print("매수 성공! 현금 잔액이 자동으로 차감되었습니다.")
```

## 데이터 저장 위치

가상 현금 데이터는 다음 위치에 저장됩니다:
```
Scripts/modules/demo_data/cash_[계좌번호].json
```

예: `Scripts/modules/demo_data/cash_12345678.json`

## 데이터 구조

```json
{
  "account": "12345678",
  "cash_balance": 9250000,
  "created_at": "2025-01-20T10:00:00",
  "updated_at": "2025-01-20T11:30:00", 
  "transaction_history": [
    {
      "timestamp": "2025-01-20T11:30:00",
      "type": "buy",
      "amount": -750000,
      "balance_before": 10000000,
      "balance_after": 9250000,
      "stock_code": "005930",
      "quantity": 10,
      "price": 75000,
      "memo": "005930 10주 매수"
    }
  ]
}
```

## 주의사항

1. **모의투자 전용**: 실전 환경에서는 실제 KIS API 사용
2. **가격 추정**: 시장가 주문 시 종목별 고정 가격 사용 (실제 시세 연동 필요 시 추가 구현)
3. **데이터 백업**: JSON 파일 수동 백업 권장
4. **계좌별 분리**: 각 계좌별로 독립적인 현금 관리

## 향후 개선 사안

1. **실시간 시세 연동**: 현재가 API를 통한 정확한 가격 적용
2. **수수료 계산**: 거래 수수료 자동 차감
3. **보유종목 관리**: 매수/매도한 종목 수량 추적
4. **데이터베이스 연동**: JSON 대신 SQLite 또는 다른 DB 사용
5. **웹 인터페이스**: 브라우저 기반 관리 도구

## 문의

기능 관련 문의나 버그 신고는 프로젝트 이슈 트래커를 이용해 주세요.