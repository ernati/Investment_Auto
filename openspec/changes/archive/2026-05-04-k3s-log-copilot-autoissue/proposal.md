## Why

k3s에서 운영 중인 서비스 Pod 로그를 1~2일 주기로 수동 수집·분석하고 GitHub Copilot에 전달하는 과정이 반복되고 있다. 로그 수집, 필터링, GitHub Issue 생성, Copilot Coding Agent 할당 단계를 자동화하여 운영 부담을 줄이고 버그 수정 주기를 단축한다.

## What Changes

- k3s CronJob으로 서비스 Pod 로그를 주기적으로 수집하는 컴포넌트 추가
- 수집된 로그에서 에러 및 코드 수정 가능 버그 후보를 필터링하는 로직 추가
- 버그 후보를 기반으로 GitHub Issue를 자동 생성하는 로직 추가
- 생성된 Issue에 GitHub Copilot Coding Agent를 자동 할당하는 로직 추가
- 아래는 이번 변경 범위에 포함하지 않음:
  - Copilot의 실제 코드 수정 및 PR 생성 (Copilot Coding Agent 역할)
  - PR 자동 승인 / 자동 merge
  - ArgoCD 강제 sync
  - 운영 Pod/Deployment 직접 수정
  - main/master 직접 push

## Capabilities

### New Capabilities

- `k3s-log-collector`: k3s 서비스 Pod 로그를 주기적으로 수집하는 CronJob 및 수집 스크립트
- `log-filter-analyzer`: 수집된 로그에서 에러·경고를 분류하고 코드 수정 가능성이 있는 버그 후보를 추출하는 필터링·분석 로직
- `github-issue-auto-creator`: 버그 후보를 정형화된 포맷으로 GitHub Issue에 자동 생성하는 로직
- `copilot-agent-assigner`: 생성된 Issue에 GitHub Copilot Coding Agent를 할당하는 로직

### Modified Capabilities

(없음 - 기존 spec의 요구사항 변경 없음)

## Impact

- **새 파일/디렉토리**: `k8s/log-collector/` (CronJob 매니페스트), `Scripts/modules/log_collector.py`, `Scripts/modules/log_analyzer.py`, `Scripts/modules/github_issue_creator.py`
- **외부 의존성**: GitHub API (PyGitHub 또는 `gh` CLI), k3s/kubectl 접근 권한
- **보안**: GitHub Personal Access Token 또는 GitHub App 자격증명 필요, 운영 클러스터 read-only 접근만 허용
- **기존 코드 영향**: 없음 (신규 컴포넌트 추가만)
