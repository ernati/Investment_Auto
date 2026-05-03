# copilot-agent-assigner

## 목적

생성된 GitHub Issue에 Copilot Coding Agent를 자동 할당하는 컴포넌트. 할당 실패 시에도 전체 파이프라인이 중단되지 않아야 한다.

---

## Requirements

### Requirement: Copilot Coding Agent Issue 할당
시스템은 생성된 GitHub Issue에 GitHub Copilot Agent(`copilot-swe-agent[bot]`)를 assignee로 자동 할당해야 한다. PyGitHub는 `agent_assignment` 파라미터를 지원하지 않으므로, GitHub REST API(`POST /repos/{owner}/{repo}/issues/{number}/assignees`)를 `requests`로 직접 호출하며 `agent_assignment` 파라미터를 함께 전달한다. `COPILOT_AGENT_USERNAME` 환경변수가 설정된 경우에만 할당을 시도한다.

- assignee: `copilot-swe-agent[bot]` (고정값, 환경변수 값과 무관)
- `COPILOT_AGENT_USERNAME` 환경변수: 할당 활성화 여부를 제어하는 스위치 역할 (값은 무시됨)
- REST API 헤더: `X-GitHub-Api-Version: 2022-11-28`

#### Scenario: 정상 할당
- **WHEN** Issue가 성공적으로 생성되고 `COPILOT_AGENT_USERNAME`이 설정되어 있으면
- **THEN** REST API를 통해 `copilot-swe-agent[bot]`이 Issue의 assignee로 등록되고 Copilot Agent가 작업을 시작한다

#### Scenario: 환경변수 미설정 시 건너뜀
- **WHEN** `COPILOT_AGENT_USERNAME` 환경변수가 설정되지 않거나 비어 있으면
- **THEN** 할당 단계를 건너뛰고 Issue는 assignee 없이 생성된다

### Requirement: 할당 실패 무중단 처리
Copilot Coding Agent 할당이 실패하더라도 전체 파이프라인이 중단되어서는 안 된다.

#### Scenario: 할당 API 실패
- **WHEN** REST API 호출이 실패하면
- **THEN** 시스템은 실패를 로그에 기록하고 나머지 Issue 처리를 계속 진행한다
