## 1. `db_manager.py` 확인 및 준비

- [x] 1.1 `save_system_log()` 메서드 시그니처와 파라미터(`level`, `module`, `message`, `extra_data`, `environment`)를 확인한다
- [x] 1.2 `save_system_log()` 내부에서 예외가 발생할 때 재발생 없이 처리되는지 확인하고, 필요하면 `try/except`로 감싼다
- [x] 1.3 `save_trading_history()`가 `status='failed'` 값을 그대로 저장할 수 있는지 확인한다

## 2. `portfolio_rebalancing.py` — 사이클 예외 및 스킵 로깅

- [x] 2.1 `run_once()` 전체 예외 `except` 블록에 `save_system_log(level='ERROR', module='rebalancing', ...)` 호출을 추가한다 (`db_manager` 활성화 시)
- [x] 2.2 `should_rebalance=False` 스킵 분기에 `save_system_log(level='INFO', module='rebalancing', message=plan.rebalance_reason)` 호출을 추가한다
- [x] 2.3 두 호출 모두 `try/except`로 감싸 로깅 실패가 실행 흐름을 방해하지 않도록 한다

## 3. `portfolio_rebalancing.py` — 실패 주문 trading_history 저장

- [x] 3.1 `_save_to_database()`에서 실패 주문 목록을 순회하는 로직을 추가한다
- [x] 3.2 각 실패 주문을 `status='failed'`, 체결가 없으면 `price=0`으로 `save_trading_history()`에 전달한다
- [x] 3.3 실패 주문 저장 실패 시 예외를 재발생시키지 않고 `logger.error()`로만 처리한다

## 4. `kis_api_utils.py` — API 최종 실패 DB 로깅

- [x] 4.1 API 호출 함수(`call_api` 또는 동등한 함수)에 `db_manager=None` 선택적 파라미터를 추가한다
- [x] 4.2 `RuntimeError` 발생 직전(재시도 소진 후) `save_system_log(level='ERROR', module='kis_api', ...)` 호출을 추가한다
- [x] 4.3 호출 지점(`portfolio_rebalancing.py`, `order_executor.py` 등)에서 `db_manager`를 넘기도록 수정한다

## 5. `order_executor.py` — 주문 실패 DB 로깅

- [x] 5.1 주문 배치/개별 주문 실패 처리 지점에 `save_system_log(level='ERROR', module='order_executor', ...)` 호출을 추가한다 (`db_manager` 전달 시)
- [x] 5.2 `db_manager` 참조를 `order_executor`의 적절한 메서드/생성자로 전달할 수 있도록 수정한다
- [x] 5.3 로깅 실패 시 예외를 재발생시키지 않고 `logger.error()`로만 처리한다

## 6. 검증

- [x] 6.1 `--db-mode` 플래그로 실행하여 에러 발생 시 `system_logs` 테이블에 레코드가 삽입되는지 확인한다
- [x] 6.2 의도적으로 주문 실패를 유발하여 `trading_history`에 `status='failed'` 레코드가 삽입되는지 확인한다
- [x] 6.3 `db_manager=None` 환경에서 기존 동작이 유지되고 예외가 발생하지 않는지 확인한다
- [x] 6.4 `save_system_log()` 자체가 실패해도 메인 실행 흐름이 계속되는지 확인한다
