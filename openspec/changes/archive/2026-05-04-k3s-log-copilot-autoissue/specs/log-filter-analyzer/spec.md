## ADDED Requirements

### Requirement: 에러 패턴 필터링
시스템은 수집된 로그에서 `ERROR`, `CRITICAL`, `Traceback (most recent call last)`, `Exception`, `FATAL` 키워드를 포함하는 라인 및 그 컨텍스트(전후 5줄)를 추출해야 한다.

#### Scenario: 에러 라인 추출
- **WHEN** 로그 텍스트가 필터링 컴포넌트에 입력되면
- **THEN** 시스템은 에러 키워드를 포함하는 라인과 전후 컨텍스트 5줄을 묶어 에러 블록으로 반환한다

#### Scenario: 에러 없는 로그 처리
- **WHEN** 로그 텍스트에 에러 키워드가 존재하지 않으면
- **THEN** 시스템은 빈 결과를 반환하고 후속 Issue 생성 단계를 건너뛴다

### Requirement: 버그 후보 중복 제거
동일한 에러 메시지(스택 트레이스 포함)가 반복 출현하는 경우, 대표 1건만 버그 후보로 포함해야 한다.

#### Scenario: 동일 에러 중복 제거
- **WHEN** 동일한 에러 패턴이 로그 내에 여러 번 등장하면
- **THEN** 첫 번째 발생 건만 버그 후보 목록에 포함되고 나머지는 제거된다

### Requirement: 버그 후보 정형화 출력
필터링된 버그 후보는 Issue 생성에 사용 가능한 구조체(제목, 에러 메시지, 로그 컨텍스트, Pod명, 발생 시각)로 변환되어야 한다.

#### Scenario: 버그 후보 구조체 생성
- **WHEN** 에러 블록이 추출되면
- **THEN** 시스템은 {title, error_message, log_context, pod_name, occurred_at} 필드를 갖는 구조체를 반환한다
