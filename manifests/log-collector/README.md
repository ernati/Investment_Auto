# k3s Log Copilot AutoIssue

k3s 클러스터의 서비스 Pod 로그를 주기적으로 수집하고, 에러를 분석하여 GitHub Issue를 자동 생성한 뒤 GitHub Copilot Coding Agent를 할당하는 파이프라인입니다.

## 아키텍처

```
CronJob (k3s)
  └─ log_autoissue_runner.py
        ├─ [1] log_collector.py     → Pod 로그 수집
        ├─ [2] log_analyzer.py      → 에러 필터링 및 버그 후보 추출
        ├─ [3] github_issue_creator.py → GitHub Issue 자동 생성
        └─ [4] github_issue_creator.py → Copilot Agent 할당
```

## 환경변수

| 변수명 | 필수 | 설명 | 예시 |
|--------|------|------|------|
| `LOG_NAMESPACE` | ✅ | 로그 수집 대상 Kubernetes namespace | `default` |
| `LOG_LABEL_SELECTOR` | ✅ | Pod 선택 label selector | `app=investment-auto` |
| `GITHUB_TOKEN` | ✅ | GitHub Personal Access Token (repo 범위 필요) | `ghp_xxxxx` |
| `GITHUB_REPO` | ✅ | 대상 GitHub 저장소 | `owner/repo` |
| `COPILOT_AGENT_USERNAME` | ❌ | Copilot Coding Agent GitHub 사용자명 (미설정 시 할당 건너뜀) | `copilot-agent` |
| `MAX_ISSUES_PER_RUN` | ❌ | 실행 당 최대 Issue 생성 수 (기본값: 5) | `3` |

## 배포 방법

### 1. GitHub Token Secret 등록

```bash
kubectl create secret generic log-collector-secrets \
  --from-literal=GITHUB_TOKEN=<your-token> \
  --from-literal=GITHUB_REPO=<owner/repo> \
  -n default
```

> **주의**: `manifests/log-collector/secret.yaml` 파일에는 실제 토큰 값을 입력하지 마세요. Secret은 위 명령으로 직접 클러스터에 주입합니다.

### 2. RBAC 및 ServiceAccount 배포

```bash
kubectl apply -f manifests/log-collector/serviceaccount.yaml
kubectl apply -f manifests/log-collector/clusterrole.yaml
kubectl apply -f manifests/log-collector/clusterrolebinding.yaml
```

### 3. CronJob 배포

`manifests/log-collector/cronjob.yaml`에서 다음 항목을 환경에 맞게 수정한 뒤 배포합니다:

- `spec.schedule`: 실행 주기 (기본: 매일 00:00 UTC)
- `containers[0].image`: 실제 Docker 이미지 태그
- `env.LOG_NAMESPACE`: 대상 namespace
- `env.LOG_LABEL_SELECTOR`: 대상 Pod label selector
- `env.COPILOT_AGENT_USERNAME`: Copilot Agent 사용자명 (선택)

```bash
kubectl apply -f manifests/log-collector/cronjob.yaml
```

### 4. 첫 실행 테스트 (수동 Job)

```bash
kubectl create job log-collector-test \
  --from=cronjob/log-collector \
  -n default
```

실행 결과 확인:

```bash
kubectl logs job/log-collector-test -n default
```

Issue가 정상 생성되면 CronJob 스케줄이 자동으로 이후 실행을 관리합니다.

## 롤백 방법

### CronJob 일시 중단

```bash
kubectl patch cronjob log-collector -n default \
  -p '{"spec": {"suspend": true}}'
```

### CronJob 완전 삭제

```bash
kubectl delete -f manifests/log-collector/
```

RBAC 리소스만 유지하고 싶다면:

```bash
kubectl delete -f manifests/log-collector/cronjob.yaml
```

## 로컬 개발 및 테스트

### 의존성 설치

```bash
pip install -r requirements.txt
pip install kubernetes
```

### 단위 테스트 실행

```bash
python -m pytest Scripts/tests/test_log_analyzer.py -v
python -m pytest Scripts/tests/test_github_issue_creator.py -v
python -m pytest Scripts/tests/test_log_collector.py -v
python -m pytest Scripts/tests/test_pipeline_integration.py -v
```

### 파이프라인 수동 실행 (로컬 kubeconfig 환경)

```bash
export LOG_NAMESPACE=default
export LOG_LABEL_SELECTOR="app=investment-auto"
export GITHUB_TOKEN=<your-token>
export GITHUB_REPO=owner/repo
export COPILOT_AGENT_USERNAME=copilot-agent  # 선택
export MAX_ISSUES_PER_RUN=3                  # 선택

python -m Scripts.apps.log_autoissue_runner
```

## 생성되는 Issue 형식

- **제목**: `[AutoBug] <에러 메시지 요약 (최대 80자)>`
- **본문**: 에러 발생 Pod, 발생 시각, 에러 메시지, 로그 컨텍스트(전후 5줄) 포함
- **Assignee**: `COPILOT_AGENT_USERNAME` 환경변수로 지정된 사용자 (설정 시)

## 주의사항

- GitHub Token은 `repo` 범위 권한이 필요합니다.
- ClusterRole은 `pods/log` 및 `pods` 리소스에 대한 `get`, `list` 권한만 부여합니다.
- 동일한 에러 패턴의 Issue가 이미 open 상태이면 중복 생성하지 않습니다.
- `MAX_ISSUES_PER_RUN`을 통해 노이즈성 Issue 대량 생성을 방지합니다.
