## Context

현재 시스템은 리밸런싱 수준의 성공/실패만 `rebalancing_logs`에 기록하고, 성공한 주문만 `trading_history`에 저장한다. `system_logs` 테이블은 스키마와 `save_system_log()` 메서드가 이미 구현되어 있으나 어디서도 호출되지 않는다. 함수/API 단위 에러는 Python `logging` 모듈(파일·콘솔)에만 남아 DB 조회만으로는 장애를 추적할 수 없다.

## Goals / Non-Goals

**Goals:**
- 기존 `system_logs` 테이블과 `save_system_log()` API를 실제 에러 발생 지점에서 호출한다.
- 실패한 개별 주문을 `trading_history`에 `status='failed'`로 기록한다.
- DB 로깅이 활성화되지 않은 경우(`db_manager=None`)에는 기존 동작을 그대로 유지한다.

**Non-Goals:**
- DB 스키마 변경 (테이블·컬럼 추가·삭제 없음)
- Python `logging` 모듈 설정 변경
- 외부 모니터링 시스템 연동
- 로그 조회 UI 또는 API 추가

## Decisions

### 1. `save_system_log()` 호출 지점 선정

기존 `logger.error()` / `logger.warning()` 호출이 있는 지점 중 유지보수에 필요한 핵심 위치에만 DB 로깅을 추가한다.

| 호출 위치 | level | module | 이유 |
|---|---|---|---|
| `portfolio_rebalancing.py` — `run_once()` 전체 예외 catch | `ERROR` | `rebalancing` | 사이클 전체 실패를 DB에 남겨야 추적 가능 |
| `portfolio_rebalancing.py` — `should_rebalance=False` 스킵 | `INFO` | `rebalancing` | 스킵 사유를 DB에 남겨 이력 조회 가능 |
| `kis_api_utils.py` — `RuntimeError` 발생 지점 (API 최종 실패) | `ERROR` | `kis_api` | 재시도 소진 후 최종 실패만 기록 (재시도 중간은 제외) |
| `order_executor.py` — 주문 배치/개별 주문 실패 | `ERROR` | `order_executor` | 주문 단위 실패 맥락 보존 |

**대안으로 고려한 방식: 데코레이터 기반 자동 로깅**
- 장점: 코드 변경 최소화
- 단점: `db_manager` 참조를 전달하기 어렵고, 로그 내용(extra_data)이 획일화됨 → 채택 안 함

### 2. 실패 주문의 `trading_history` 저장 위치

실패한 주문 정보는 `order_executor.py`의 `OrderResult`에 이미 담겨 있다. `portfolio_rebalancing.py`의 `_save_to_database()`에서 실패 주문을 순회하여 `status='failed'`로 저장한다.

- `quantity`, `price` 등 일부 값이 0 또는 추정값일 수 있으므로 가능한 값만 채우고 나머지는 0으로 저장한다.
- 실패 주문 저장 실패 시 예외를 재발생시키지 않고 `logger.error()`로만 처리한다 (로깅 실패가 실행 흐름을 방해하지 않도록).

### 3. `db_manager` 참조 전달

`kis_api_utils.py`는 현재 `db_manager`를 전달받지 않는다. API 에러를 DB에 기록하려면 참조가 필요하다.

**선택: 선택적 파라미터로 전달**
```python
def call_api(..., db_manager=None):
    ...
    if db_manager:
        db_manager.save_system_log(...)
```
- 기존 호출 코드 변경 최소화
- `None` 기본값으로 하위 호환성 유지

## Risks / Trade-offs

- **로깅 실패가 실행 흐름을 방해할 위험** → `save_system_log()` 호출을 `try/except`로 감싸고 내부에서만 `logger.error()`로 처리한다.
- **`kis_api_utils.py` 시그니처 변경** → 호출 지점(`portfolio_rebalancing.py`, `order_executor.py` 등)에서 `db_manager`를 넘겨야 하므로 호출 코드도 수정이 필요하다.
- **실패 주문의 가격 정보 부정확** → 주문 실패 시점에 체결가가 없을 수 있어 0 또는 요청가로 기록된다. 이 점을 `extra_data` JSON에 명시한다.

## Migration Plan

1. 코드 변경 후 `--db-mode` 플래그로 실행하여 `system_logs` 테이블에 레코드가 삽입되는지 확인한다.
2. 롤백 전략: `save_system_log()` 호출 제거만으로 원복 가능 (스키마 변경 없음).

## Open Questions

- `kis_api_utils.py`에서 재시도 중간 에러(Rate Limit, 토큰 만료)도 DB에 기록할 것인가, 아니면 최종 실패만 기록할 것인가? → 현재 설계는 **최종 실패만** 기록 (재시도 중간 로그는 노이즈가 될 수 있음).
