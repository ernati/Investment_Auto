## Why

현재 DB에는 리밸런싱 수준의 성공/실패만 기록되고, 개별 주문 실패·함수 단위 예외·API 에러 등 세부 실패 정보는 Python 로그(파일/콘솔)에만 남아 있다. `system_logs` 테이블이 이미 스키마로 정의되어 있으나 실제로 사용되지 않고 있으며, 이로 인해 운영 중 발생한 장애를 DB만으로는 추적할 수 없어 유지보수가 어렵다.

## What Changes

- `system_logs` 테이블을 실제로 활용하도록 `db_manager.save_system_log()` 호출 코드를 추가한다.
- 개별 주문 실패(`status='failed'`)를 `trading_history`에 기록한다 (현재는 성공한 주문만 저장됨).
- 리밸런싱 사이클 예외(`run_once()` 전체 예외)를 `system_logs`에 기록한다.
- KIS API 에러(HTTP 오류, Rate Limit, 토큰 만료 등)를 `system_logs`에 기록한다.
- 리밸런싱 스킵 사유(`should_rebalance=False`)를 `system_logs`에 기록한다.
- 가드레일 조정 이벤트(주문 수량/개수 축소)를 `system_logs`에 기록한다.

## Capabilities

### New Capabilities

- `function-error-logging`: 함수/모듈 단위 실패 및 예외를 `system_logs` DB 테이블에 기록하는 기능. `save_system_log()` 호출 지점을 주요 에러 발생 위치에 추가한다.
- `failed-order-logging`: 실패한 개별 주문을 `trading_history` 테이블에 `status='failed'`로 기록하는 기능.

### Modified Capabilities

- `rebalancing-execution`: 리밸런싱 사이클 예외 및 스킵 사유를 DB에 기록하도록 실행 흐름 수정. (`Scripts/apps/portfolio_rebalancing.py`)

## Impact

- **수정 파일**:
  - `Scripts/apps/portfolio_rebalancing.py` — 사이클 예외·스킵 사유 로깅 추가
  - `Scripts/modules/db_manager.py` — `save_system_log()` 및 실패 주문 저장 경로 확인
  - `Scripts/modules/kis_api_utils.py` — API 에러 시 `save_system_log()` 호출 추가
  - `Scripts/modules/order_executor.py` — 주문 실패 시 `trading_history` 저장 추가
- **DB**: `system_logs` 테이블 (기존 스키마 변경 없음), `trading_history` (기존 스키마 변경 없음)
- **인터페이스 변경**: 없음 (내부 로깅 확장만)
- **Breaking Change**: 없음
