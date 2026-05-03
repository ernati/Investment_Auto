전체 그림을 설명하겠습니다.
---
구현된 기능 사용 가이드
전체 흐름
k3s CronJob (매일 00:00 UTC)
    │
    ▼
log_autoissue_runner.py  ← 진입점
    │
    ├─ [1] log_collector.py
    │       kubernetes 클라이언트로 지정 namespace의 Pod 로그 수집
    │       → {pod_name: log_text} 딕셔너리
    │
    ├─ [2] log_analyzer.py
    │       ERROR / CRITICAL / Traceback / Exception / FATAL 키워드 추출
    │       전후 5줄 컨텍스트 포함, 중복 패턴 제거
    │       → [{title, error_message, log_context, pod_name, occurred_at}]
    │
    ├─ [3] github_issue_creator.py
    │       PyGitHub로 GitHub Issue 자동 생성
    │       제목: [AutoBug] <에러 요약>
    │       동일 제목 open Issue 있으면 건너뜀
    │       MAX_ISSUES_PER_RUN 한도 적용
    │
    └─ [4] github_issue_creator.py
            COPILOT_AGENT_USERNAME으로 Copilot Coding Agent 할당
---
1단계 — 사전 준비
GitHub Token Secret을 클러스터에 등록합니다.
kubectl create secret generic log-collector-secrets \
  --from-literal=GITHUB_TOKEN=ghp_xxxxxxxx \
  --from-literal=GITHUB_REPO=your-org/your-repo \
  -n default
GITHUB_TOKEN은 해당 저장소의 issues: write 권한이 있어야 합니다.
---
2단계 — CronJob 배포
manifests/log-collector/cronjob.yaml에서 두 가지를 실제 환경에 맞게 수정합니다.
# 수집 대상 namespace / label selector
- name: LOG_NAMESPACE
  value: "default"          # ← 실제 namespace로 변경
- name: LOG_LABEL_SELECTOR
  value: "app=investment-auto"  # ← 실제 label로 변경
# Copilot Agent 할당 (선택)
- name: COPILOT_AGENT_USERNAME
  value: ""                 # ← Copilot Agent의 GitHub username 입력
# 이미지 (현재 python:3.11-slim — 실제 배포 이미지로 교체 필요)
image: python:3.11-slim     # ← 프로젝트 Docker 이미지로 교체
수정 후 배포합니다.
kubectl apply -f manifests/log-collector/serviceaccount.yaml
kubectl apply -f manifests/log-collector/clusterrole.yaml
kubectl apply -f manifests/log-collector/clusterrolebinding.yaml
kubectl apply -f manifests/log-collector/cronjob.yaml
---
3단계 — 첫 실행 수동 테스트
스케줄 전에 수동으로 한 번 실행해서 정상 동작을 확인합니다.
# Job 수동 실행
kubectl create job log-collector-test \
  --from=cronjob/log-collector -n default
# 로그 확인
kubectl logs job/log-collector-test -n default
정상 실행 시 다음과 같은 로그가 출력됩니다.
2026-05-04T00:00:00 [INFO] __main__: k3s-log-copilot-autoissue 파이프라인 시작
2026-05-04T00:00:01 [INFO] __main__: === [1/4] Pod 로그 수집 시작 ===
2026-05-04T00:00:02 [INFO] __main__: 로그 수집 완료: 3개 Pod
2026-05-04T00:00:02 [INFO] __main__: === [2/4] 에러 분석 및 버그 후보 추출 시작 ===
2026-05-04T00:00:02 [INFO] __main__: 버그 후보 2개 추출
2026-05-04T00:00:03 [INFO] __main__: === [3/4] GitHub Issue 생성 시작 ===
2026-05-04T00:00:04 [INFO] __main__: Issue 생성 완료: 2개
2026-05-04T00:00:04 [INFO] __main__: === [4/4] Copilot Agent 할당 시작 ===
2026-05-04T00:00:05 [INFO] __main__: 파이프라인 완료 — Issue 생성: 2개, Copilot 할당: 2개
GitHub 저장소의 Issues 탭에서 [AutoBug] 접두사가 붙은 Issue가 생성되었는지 확인합니다.
---
로컬에서 직접 실행 (선택)
클러스터 없이 로컬 kubeconfig 환경에서도 실행할 수 있습니다.
# 의존성 설치
pip install PyGitHub kubernetes
# 환경변수 설정 후 실행
export LOG_NAMESPACE=default
export LOG_LABEL_SELECTOR="app=investment-auto"
export GITHUB_TOKEN=ghp_xxxxxxxx
export GITHUB_REPO=your-org/your-repo
export COPILOT_AGENT_USERNAME=copilot-agent   # 선택
export MAX_ISSUES_PER_RUN=3                   # 선택, 기본 5
python -m Scripts.apps.log_autoissue_runner
---
주요 동작 규칙 요약
상황	동작
특정 Pod 로그 수집 실패	해당 Pod 건너뛰고 나머지 계속
에러 없는 로그	Issue 생성 없이 정상 종료
동일 에러 패턴 반복	첫 번째 발생 건만 후보로 포함
동일 제목 open Issue 존재	중복 생성 건너뜀
MAX_ISSUES_PER_RUN 초과	한도 이후 후보는 모두 건너뜀
COPILOT_AGENT_USERNAME 미설정	할당 단계 건너뜀, Issue는 정상 생성
Copilot Agent 할당 실패	로그 기록 후 파이프라인 계속 진행
---
현재 미완성 항목 (배포 전 필요)
cronjob.yaml의 image: python:3.11-slim은 임시 이미지입니다. 실제 배포 시에는 프로젝트 코드가 포함된 Docker 이미지를 빌드해서 지정해야 합니다. python:3.11-slim에는 Scripts/ 코드가 포함되어 있지 않아 그대로 사용하면 실행에 실패합니다.