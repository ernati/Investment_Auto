# KIS API Rate Limiting 문제 해결 가이드

## 문제 상황

KIS API 호출 시 `[EGW00201] 초당 거래건수를 초과하였습니다.` 오류가 발생하는 문제입니다. 이는 KIS API의 Rate Limiting 정책으로 인해 발생하며, API 호출 빈도가 허용 한도를 초과할 때 나타납니다.

## 문제 원인

1. **Rate Limiting 제약**: KIS API는 초당 호출 횟수에 제한을 두고 있음
2. **연속적인 API 호출**: 포트폴리오 조회나 다수 종목 가격 조회 시 연속적인 API 호출 발생
3. **재시도 로직 부재**: 일시적 오류 발생 시 적절한 백오프 전략 없음

## 해결 방법

### 1. Rate Limiting 지연 추가

#### `kis_api_utils.py` 수정사항

**smart_sleep 함수 추가:**
```python
def smart_sleep(env: str = "demo", debug: bool = False) -> None:
    """
    KIS API 호출 사이에 적절한 지연을 추가하여 rate limiting을 방지합니다.
    
    Args:
        env (str): 환경 ("demo" 또는 "real")
        debug (bool): 디버그 로그 출력 여부
    """
    delay = _RATE_LIMIT_DELAY.get(env, 0.5)
    
    if debug:
        logger.debug(f"[RateLimit] Sleeping {delay}s for {env} environment")
    
    time.sleep(delay)
```

**지연 시간 설정:**
- 모의투자 환경: 0.5초
- 실전투자 환경: 0.1초

### 2. 백오프 전략이 적용된 재시도 로직

#### `execute_api_request_with_retry` 함수 구현

**주요 특징:**
- 지수적 백오프 (Exponential Backoff) 적용
- 지터(Jitter) 추가로 동시 요청 분산
- Rate limiting 오류 자동 감지
- 최대 재시도 횟수 제한

**백오프 공식:**
```
총 지연시간 = 기본지연시간 × (2^(재시도횟수-1)) × 지터계수
지터계수 = 0.5 ~ 1.5 (랜덤)
```

### 3. API 호출 지점 수정

#### 수정된 함수들

1. **계좌 잔고 조회** (`fetch_account_balance`)
2. **보유종목 조회** (`fetch_holdings`) 
3. **가격 조회** (`fetch_current_price`)
4. **주식 주문** (`place_stock_order`)

모든 API 호출에서 `execute_api_request_with_retry` 함수 사용으로 변경됨.

## 적용된 변경사항 요약

### 📁 `Scripts/modules/kis_api_utils.py`

1. **smart_sleep 함수 추가**: 환경별 적절한 지연 시간 적용
2. **execute_api_request_with_retry 함수 추가**: 
   - 지수적 백오프 재시도 로직
   - Rate limiting 오류 자동 감지 및 재시도
   - 지터 적용으로 동시 요청 분산
3. **place_stock_order 함수 수정**: 새로운 재시도 로직 적용

### 📁 `Scripts/modules/kis_trading.py`

1. **import 문 수정**: `execute_api_request_with_retry`, `build_api_headers` 사용
2. **_call_api 함수 수정**: Rate limiting이 적용된 API 호출로 변경
3. **기존 requests 직접 사용 제거**: 모든 API 호출이 통합된 유틸리티 사용

### 📁 `Scripts/modules/kis_portfolio_fetcher.py`

1. **import 문 수정**: `execute_api_request_with_retry` 사용
2. **모든 API 호출 지점 수정**: 
   - `fetch_account_balance`
   - `fetch_holdings`
   - `fetch_current_price`
   - `_fetch_balance_via_holdings`

## 사용법

수정된 코드는 기존 인터페이스와 동일하게 작동합니다. 추가 설정이나 변경 없이 기존 코드가 자동으로 새로운 Rate Limiting 로직을 사용합니다.

### 환경별 지연 시간

```python
# 모의투자 환경 (demo)
smart_sleep("demo")  # 0.5초 지연

# 실전투자 환경 (real)  
smart_sleep("real")  # 0.1초 지연
```

### 재시도 설정

기본 설정:
- **최대 재시도**: 3회
- **기본 지연**: 1.0초
- **백오프 방식**: 지수적 증가 (1초 → 2초 → 4초)
- **지터**: 50%-150% 랜덤

## 추가 권장사항

1. **로그 레벨 조정**: Rate limiting 관련 로그 확인을 위해 DEBUG 레벨 사용 고려
2. **동시 요청 제한**: 가능한 한 순차적 API 호출 권장  
3. **캐싱 활용**: 동일한 데이터의 반복 조회 방지
4. **배치 처리**: 여러 종목 조회 시 배치 단위로 지연 적용

## 테스트 방법

1. **기존 스크립트 실행**: 동일한 명령어로 실행하여 오류 발생 여부 확인
   ```bash
   python .\Scripts\apps\portfolio_rebalancing.py --demo --mode schedule
   ```

2. **로그 확인**: Rate limiting 관련 WARNING/ERROR 로그 모니터링
   - `[EGW00201]` 오류 메시지가 사라졌는지 확인
   - API 호출 사이에 적절한 지연이 적용되는지 확인

3. **성능 측정**: 전체 실행 시간 증가 확인 (지연으로 인한 자연스러운 증가)

수정된 코드는 안정성을 높이면서도 기존 기능을 그대로 유지합니다. Rate limiting 오류가 발생하지 않아 더 안정적인 포트폴리오 리밸런싱이 가능합니다.

## 수정사항 요약

✅ **해결된 문제**: `[EGW00201] 초당 거래건수를 초과하였습니다.` 에러  
✅ **적용된 해결책**: 
- Rate limiting 지연 (모의: 0.5초, 실전: 0.1초)
- 지수적 백오프 재시도 로직
- 지터 적용으로 동시 요청 분산
- 모든 API 호출 지점 통합 관리

✅ **수정된 모듈**:
- `kis_api_utils.py` - Rate limiting 및 재시도 로직 추가
- `kis_portfolio_fetcher.py` - 포트폴리오 조회 API 호출 수정
- `kis_trading.py` - 거래 주문 API 호출 수정
- `order_executor.py` - 기존 place_stock_order 사용 (자동 적용됨)