## ADDED Requirements

### Requirement: Copilot Coding Agent Issue 할당
시스템은 생성된 GitHub Issue에 `COPILOT_AGENT_USERNAME` 환경변수로 지정된 GitHub 사용자를 assignee로 자동 할당해야 한다.

#### Scenario: 정상 할당
- **WHEN** Issue가 성공적으로 생성되고 COPILOT_AGENT_USERNAME이 설정되어 있으면
- **THEN** 해당 GitHub 사용자가 Issue의 assignee로 등록된다

#### Scenario: 환경변수 미설정 시 건너뜀
- **WHEN** COPILOT_AGENT_USERNAME 환경변수가 설정되지 않거나 비어 있으면
- **THEN** 할당 단계를 건너뛰고 Issue는 assignee 없이 생성된다

### Requirement: 할당 실패 무중단 처리
Copilot Coding Agent 할당이 실패하더라도 전체 파이프라인이 중단되어서는 안 된다.

#### Scenario: 할당 API 실패
- **WHEN** assignee 설정 API 호출이 실패하면
- **THEN** 시스템은 실패를 로그에 기록하고 나머지 Issue 처리를 계속 진행한다
