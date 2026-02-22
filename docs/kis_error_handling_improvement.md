# KIS API 에러 처리 개선

## 개요

포트폴리오 리밸런싱 스크립트에서 한국투자증권 API 호출 실패 시 HTTP 상태 코드만 출력되던 문제를 해결하여, 실제 KIS API의 상세한 에러 메시지를 출력하도록 개선했습니다.

## 문제 상황

기존에 portfolio_rebalancing.py 실행 시 다음과 같이 HTTP 에러만 표시되었습니다:

```
2026-02-16 11:21:27,387 - modules.kis_api_utils - ERROR - Stock order (market buy): HTTP error - 500 Server Error: Internal Server Error for url: https://openapivts.koreainvestment.com:29443/uapi/domestic-stock/v1/trading/order-cash
```

반면 samsung_auto_trading.py와 bond_trading_demo.py에서는 상세한 에러 메시지가 출력되었습니다:

```
[ERROR] 2026-02-16 11:22:51 - ✗ 매수 주문 실패: [40100000] 모의투자 영업일이 아닙니다.
❌ 채권 정보 조회 실패: 없는 서비스 코드 입니다
```

## 해결 방법

### 1. KIS API 응답 구조 분석

한국투자증권 API는 HTTP 500 에러를 반환할 때도 response body에 다음과 같은 구조로 실제 에러 정보를 포함합니다:

```json
{
    "rt_cd": "1",           // 결과 코드 ("0": 성공, "1": 실패)
    "msg_cd": "40100000",   // 에러 코드
    "msg1": "모의투자 영업일이 아닙니다."  // 에러 메시지
}
```

### 2. 수정된 파일들

#### `kis_api_utils.py`

**execute_api_request 함수 개선:**
- HTTP 에러 발생 시 response body에서 KIS API 에러 정보 추출
- `msg_cd`와 `msg1` 필드를 조합하여 상세한 에러 메시지 생성

**place_stock_order 함수 개선:**
- Exception 처리 시 KIS API 에러 메시지만 추출하여 반환
- 불필요한 context 정보 제거

#### `kis_portfolio_fetcher.py`

**fetch_current_price 함수 개선:**
- 가격 조회 실패 시 상세한 에러 메시지 표시
- 재시도 로그와 최종 에러 로그에 KIS API 에러 메시지 포함

#### `order_executor.py`

**_execute_order_live 함수 개선:**
- 주문 실행 실패 시 상세한 에러 메시지 추출
- RuntimeError 전달 시 KIS API 에러 메시지만 포함

## 개선 결과

이제 portfolio 스크립트에서도 다음과 같은 상세한 에러 메시지가 출력됩니다:

```
ERROR - KIS API error - [40100000] 모의투자 영업일이 아닙니다. (HTTP 500)
ERROR - Plan execution failed: [40100000] 모의투자 영업일이 아닙니다.
```

## 에러 처리 로직

### 1. HTTP 에러 시 response body 확인

```python
except requests.exceptions.HTTPError as e:
    # HTTP 에러 시에도 response body에서 KIS API 에러 메시지 추출 시도
    try:
        if response.content:
            error_data = response.json()
            rt_cd = error_data.get('rt_cd', '')
            msg_cd = error_data.get('msg_cd', '')
            msg1 = error_data.get('msg1', '')
            
            if msg_cd or msg1:
                detailed_error = f"[{msg_cd}] {msg1}" if msg_cd else msg1
                logger.error(f"{context}: KIS API error - {detailed_error} (HTTP {response.status_code})")
                raise RuntimeError(f"{context}: {detailed_error}")
    except (ValueError, KeyError):
        pass  # JSON 파싱 실패 시 기본 HTTP 에러 메시지 사용
```

### 2. 에러 메시지 정제

RuntimeError에서 KIS API 에러 메시지만 추출:

```python
error_msg = str(e)
if isinstance(e, RuntimeError) and "KIS API error" in error_msg:
    if " - " in error_msg:
        error_msg = error_msg.split(" - ", 1)[1]  # "KIS API error - [에러코드] 메시지"에서 "[에러코드] 메시지"만 추출
```

## 참고 자료

- **open-trading-api 저장소**: 에러 처리 패턴 참조
- **KIS API 응답 구조**: `rt_cd`, `msg_cd`, `msg1` 필드 활용
- **기존 동작하는 스크립트**: samsung_auto_trading.py, bond_trading_demo.py의 에러 처리 방식

## 테스트 방법

1. 모의투자 영업일이 아닌 시간에 portfolio_rebalancing.py 실행
2. 존재하지 않는 종목코드로 가격 조회
3. 잘못된 주문 파라미터로 주문 실행

이제 이러한 경우에 HTTP 에러 대신 한국투자증권 API의 실제 에러 메시지가 출력됩니다.