# Spec: rebalancing-execution

## 목적

리밸런싱 실행 흐름에서 발생하는 스킵 이벤트를 DB에 기록하여 운영 이력을 보존한다.

## Requirements

### Requirement: 리밸런싱 스킵 사유를 system_logs에 기록한다
시스템은 리밸런싱이 필요하지 않아 스킵되는 경우(`should_rebalance=False`) 스킵 사유를 `system_logs` 테이블에 기록해야 한다(SHALL). 현재는 Python 로그에만 남으며 DB에 이력이 없다.

#### Scenario: 리밸런싱 스킵 시 DB 기록
- **WHEN** `plan.should_rebalance`가 `False`이고 `db_manager`가 활성화되어 있을 때
- **THEN** `system_logs`에 `level='INFO'`, `module='rebalancing'`, 스킵 사유(`rebalance_reason`)를 포함한 레코드가 삽입되어야 한다

#### Scenario: DB 로깅이 비활성화된 경우 기존 동작 유지
- **WHEN** `db_manager`가 `None`인 상태에서 리밸런싱이 스킵될 때
- **THEN** DB 기록 없이 기존 Python `logging` 출력만 수행하고 실행을 종료해야 한다
