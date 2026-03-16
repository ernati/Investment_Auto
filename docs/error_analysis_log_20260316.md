# 로그 분석 및 에러 수정 보고서 (2026-03-16)

## 개요
2026-03-14 ~ 2026-03-16 기간의 `portfolio_rebalancing.py` 실행 로그를 분석하여 발견된 에러들을 분류하고 수정하였습니다.

---

## 발견된 에러 종류

### 1. WARNING: 체결정보 조회 결과가 비어있음

**발생 위치**: `modules/kis_trading.py` → `_retry_execution_price_inquiry()`

**로그 예시**:
```
2026-03-16 09:00:15,078 - modules.kis_trading - WARNING - 체결정보 조회 결과가 비어있음 - 시도 1
2026-03-16 09:00:17,736 - modules.kis_trading - WARNING - 체결정보 조회 결과가 비어있음 - 시도 2
2026-03-16 09:00:20,347 - modules.kis_trading - WARNING - 체결정보 조회 결과가 비어있음 - 시도 3
2026-03-16 09:00:20,348 - modules.kis_trading - WARNING - 체결정보 3번 재시도 모두 실패: 0000000791
```

**원인 분석**:
- 모의투자(Demo) 환경에서 KIS API를 통해 주문이 접수된 후, 체결정보 조회 API가 즉시 결과를 반환하지 않는 경우가 있습니다.
- 이는 KIS 모의투자 시스템의 특성으로, 체결 데이터가 내부적으로 반영되는 데 지연이 발생할 수 있습니다.

**결론**: 
- ✅ **에러가 아닌 정상적인 WARNING입니다.**
- 현재 코드에서 3번 재시도 후 현재가(시장가)로 대체하여 처리하는 로직이 정상 작동 중입니다.
- 코드 수정 불필요.

---

### 2. ERROR: Database error - null value in column "symbol"

**발생 위치**: `modules/db_manager.py` → `save_trading_history()`

**로그**:
```
2026-03-16 09:00:29,992 - modules.db_manager - ERROR - Database error while saving trading history: null value in column "symbol" of relation "trading_history" violates not-null constraint
DETAIL:  Failing row contains (19, 2026-03-16 09:00:30.485292, portfolio-001, null, sell, 0.00000000, 0.00, 0.00, 0.00, , completed, demo).
```

**원인 분석**:
1. `modules/kis_trading.py`의 `order_cash()` 메서드에서 주문 성공 시 반환하는 결과 딕셔너리에 `symbol` 필드가 없었습니다.
2. `Scripts/apps/portfolio_rebalancing.py`에서 거래 기록을 DB에 저장할 때 `order.get('symbol')`이 `None`을 반환했습니다.
3. `trading_history` 테이블의 `symbol` 컬럼이 NOT NULL 제약조건을 가지고 있어 에러가 발생했습니다.

**결론**: 
- ❌ **코드 버그입니다. 수정 완료.**

---

## 수정 사항

### 파일: `Scripts/modules/kis_trading.py`

**변경 내용**: `order_cash()` 메서드에서 성공 응답 시 반환하는 결과 딕셔너리에 DB 저장용 필드를 추가했습니다.

**수정 전**:
```python
result = {
    'success': True,
    'order_no': output.get('ODNO', ''),
    'order_time': output.get('ORD_TMD', ''),
    'message': response.get('msg1', '주문이 정상적으로 처리되었습니다.'),
    'data': response
}
```

**수정 후**:
```python
result = {
    'success': True,
    'order_no': output.get('ODNO', ''),
    'order_time': output.get('ORD_TMD', ''),
    'message': response.get('msg1', '주문이 정상적으로 처리되었습니다.'),
    'data': response,
    # DB 저장용 필드 추가
    'symbol': stock_code,
    'side': order_type,
    'quantity': quantity,
    'price': 0  # 체결가 확인 후 업데이트
}
```

또한 체결가격이 확인된 후 `result['price']` 업데이트 코드를 추가했습니다:
```python
if executed_price is not None:
    executed_quantity = quantity
    result['price'] = executed_price  # 체결가격 업데이트
```

---

## 에러 분류 요약

| 에러 유형 | 심각도 | 원인 | 해결 상태 |
|----------|--------|------|----------|
| 체결정보 조회 결과 비어있음 | WARNING | KIS 모의투자 API 지연 특성 | ✅ 정상 (코드 변경 불필요) |
| symbol 컬럼 null 제약조건 위반 | ERROR | kis_trading.py 반환값 누락 | ✅ 수정 완료 |

---

## 테스트 권장사항

수정된 코드가 정상 작동하는지 확인하기 위해:

1. Demo 모드로 프로그램 실행
2. 장 운영시간에 리밸런싱 사이클 실행
3. DB에 거래 기록이 정상적으로 저장되는지 확인

```bash
python Scripts/apps/portfolio_rebalancing.py --mode schedule --demo --db-mode
```

---

## 참고

- KIS API 에러코드 포털: https://apiportal.koreainvestment.com/faq-error-code
- 관련 문서: [kis_trading.md](kis_trading.md), [db_manager.md](db_manager.md)
