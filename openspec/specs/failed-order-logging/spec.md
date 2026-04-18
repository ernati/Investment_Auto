# Spec: failed-order-logging

## 목적

리밸런싱 실행 중 실패한 주문을 `trading_history` 테이블에 기록하여 주문 실패 이력을 보존한다.

## Requirements

### Requirement: 실패한 주문을 trading_history에 기록한다
시스템은 실행 중 실패한 개별 주문을 `trading_history` 테이블에 `status='failed'`로 기록해야 한다(SHALL). 현재는 성공한 주문(`status='completed'`)만 저장되며, 실패 주문은 DB에 남지 않는다.

기록 시 가용한 값(symbol, order_type, quantity, price 등)을 채우고, 체결가가 없는 경우 `price=0`으로 기록한다. 실패 사유는 `extra_data` JSON에 포함되어야 한다(SHALL).

#### Scenario: 주문 실패 시 trading_history에 실패 레코드 삽입
- **WHEN** 리밸런싱 실행 중 개별 주문이 실패하고 `db_manager`가 활성화되어 있을 때
- **THEN** 해당 주문 정보가 `trading_history`에 `status='failed'`로 삽입되어야 한다

#### Scenario: 실패 주문의 체결가 없는 경우
- **WHEN** 주문 실패로 체결가를 알 수 없을 때
- **THEN** `price=0`, `total_amount=0`으로 저장하고 `extra_data`에 실패 사유를 포함해야 한다

#### Scenario: 실패 주문 DB 저장 자체가 실패한 경우
- **WHEN** 실패 주문을 `trading_history`에 삽입하는 중 DB 예외가 발생할 때
- **THEN** 해당 예외를 재발생시키지 않고 `logger.error()`로만 처리하며 리밸런싱 실행 흐름을 계속해야 한다

#### Scenario: DB 로깅이 비활성화된 경우 기존 동작 유지
- **WHEN** `db_manager`가 `None`인 상태에서 주문이 실패할 때
- **THEN** DB 기록 없이 기존 동작을 유지해야 한다
