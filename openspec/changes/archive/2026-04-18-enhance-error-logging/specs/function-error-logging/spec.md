## ADDED Requirements

### Requirement: 함수/모듈 에러를 system_logs에 기록한다
시스템은 주요 함수 및 모듈에서 발생하는 예외와 API 최종 실패를 `system_logs` 테이블에 기록해야 한다(SHALL). 기록 대상은 다음과 같다:
- 리밸런싱 사이클 전체 예외 (`run_once()`)
- KIS API 최종 실패 (재시도 소진 후)
- 주문 배치/개별 주문 실패

기록 시 `level`, `module`, `message`, `extra_data`(JSON), `environment` 필드를 채워야 한다(SHALL).

#### Scenario: 리밸런싱 사이클 예외 발생 시 DB 기록
- **WHEN** `run_once()`에서 처리되지 않은 예외가 발생하고 `db_manager`가 활성화되어 있을 때
- **THEN** `system_logs`에 `level='ERROR'`, `module='rebalancing'`, 예외 메시지와 traceback을 포함한 레코드가 삽입되어야 한다

#### Scenario: KIS API 최종 실패 시 DB 기록
- **WHEN** KIS API 호출이 최대 재시도 횟수를 초과하여 `RuntimeError`가 발생하고 `db_manager`가 전달되어 있을 때
- **THEN** `system_logs`에 `level='ERROR'`, `module='kis_api'`, 실패한 API context와 에러 메시지를 포함한 레코드가 삽입되어야 한다

#### Scenario: 주문 배치 실패 시 DB 기록
- **WHEN** `order_executor`에서 주문 실행 중 예외가 발생하고 `db_manager`가 활성화되어 있을 때
- **THEN** `system_logs`에 `level='ERROR'`, `module='order_executor'`, 실패 관련 정보를 포함한 레코드가 삽입되어야 한다

#### Scenario: DB 로깅이 비활성화된 경우 기존 동작 유지
- **WHEN** `db_manager`가 `None`인 상태에서 에러가 발생할 때
- **THEN** DB 기록 없이 기존 Python `logging` 모듈 출력만 수행해야 하며, 실행 흐름에 영향을 주어서는 안 된다

#### Scenario: system_logs 저장 자체가 실패한 경우
- **WHEN** `save_system_log()` 호출 중 DB 예외가 발생할 때
- **THEN** 해당 예외를 재발생시키지 않고 `logger.error()`로만 처리하며 실행을 계속해야 한다
