## Context

현재 k3s 클러스터에서 자동 투자 서비스가 운영 중이다. 운영자가 1~2일 주기로 Pod 로그를 수동으로 수집·분석하고, 에러가 발견되면 Copilot에 전달해 코드 수정 방향을 얻는다. 이 과정의 앞단(로그 수집 → 필터링 → Issue 생성 → Copilot 할당)을 자동화한다.

기존 코드베이스는 Python 기반 `Scripts/modules/`에 모듈화되어 있으며, k8s 매니페스트는 `k8s/` 디렉토리에 관리된다.

## Goals / Non-Goals

**Goals:**
- k3s CronJob으로 서비스 Pod 로그를 주기적으로 수집
- 수집 로그에서 ERROR/CRITICAL 레벨 및 코드 수정 가능성이 있는 패턴 필터링
- 버그 후보를 정형화된 포맷으로 GitHub Issue 자동 생성
- 생성된 Issue에 GitHub Copilot Coding Agent 자동 할당

**Non-Goals:**
- Copilot의 실제 코드 수정 및 PR 생성
- PR 자동 승인 / 자동 merge
- ArgoCD 강제 sync
- 운영 Pod/Deployment 직접 수정
- main/master 직접 push

## Decisions

### 1. 실행 방식: k3s CronJob vs 외부 스케줄러

**선택: k3s CronJob**

k3s 클러스터 내부에서 kubectl 접근이 가능하므로, 별도 외부 스케줄러(GitHub Actions, cron) 없이 CronJob으로 실행한다. 클러스터 내부 ServiceAccount에 로그 read 권한만 부여하여 최소 권한 원칙을 지킨다.

대안: GitHub Actions scheduled workflow → 외부에서 클러스터에 접근하는 구성이 추가되어 복잡도 증가, 채택 안 함.

### 2. 로그 필터링 방식: 정규식 기반 vs LLM 기반

**선택: 정규식 + 키워드 기반 필터링 (1차), LLM 확장 고려는 추후**

초기에는 `ERROR`, `CRITICAL`, `Traceback`, `Exception` 등 키워드와 정규식으로 버그 후보를 추출한다. LLM 호출은 비용·지연·신뢰성 이슈로 이번 변경에서 포함하지 않는다.

### 3. GitHub Issue 생성 방식: PyGitHub vs `gh` CLI

**선택: PyGitHub**

Python 스크립트 내에서 직접 호출 가능하고, 테스트 작성이 용이하다. `gh` CLI는 CronJob 컨테이너 이미지에 별도 설치가 필요하여 채택 안 함.

### 4. 중복 Issue 방지 전략

동일한 에러 패턴에 대해 Issue가 중복 생성되지 않도록, Issue 생성 전에 기존 open Issue의 제목에서 동일 패턴 존재 여부를 확인한다. 동일 패턴이 이미 open 상태이면 생성을 건너뛴다.

### 5. Copilot Coding Agent 할당 방식

GitHub API의 `assignees` 파라미터로 Issue 생성 시 또는 생성 후 assign한다. Copilot Coding Agent의 GitHub username을 환경변수(`COPILOT_AGENT_USERNAME`)로 주입한다.

## Risks / Trade-offs

- **[Risk] kubectl 권한 과잉** → CronJob ServiceAccount에 `logs` verb만 허용하는 ClusterRole 최소 권한으로 제한
- **[Risk] 노이즈성 Issue 대량 생성** → 동일 에러 패턴 중복 체크, 일일 최대 Issue 생성 수 제한(`MAX_ISSUES_PER_RUN` 환경변수)
- **[Risk] GitHub API rate limit** → PyGitHub의 rate limit 핸들링, 필요 시 retry with backoff
- **[Risk] GitHub Token 탈취** → k8s Secret으로 관리, 환경변수 주입, 코드에 직접 포함 금지
- **[Trade-off] 정규식 필터링의 정밀도 한계** → false positive 가능성 있음. 운영자가 Issue를 최종 검토하므로 허용 가능한 수준으로 판단

## Migration Plan

1. k8s Secret에 GitHub Token 등록
2. `k8s/log-collector/` 매니페스트 apply (ServiceAccount, ClusterRole, CronJob)
3. 첫 실행은 수동 Job으로 테스트 (`kubectl create job --from=cronjob/...`)
4. 결과 Issue 확인 후 CronJob 스케줄 활성화

롤백: CronJob 삭제 또는 suspend로 즉시 비활성화 가능.

## Open Questions

- Copilot Coding Agent의 GitHub username이 확정되어 있지 않음 → 환경변수로 분리하여 배포 시 주입
- 로그 수집 대상 namespace/label selector → 환경변수로 설정 가능하게 구현
