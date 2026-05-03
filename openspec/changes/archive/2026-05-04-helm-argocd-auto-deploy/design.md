## Context

`deployment/helm/values.yaml`에는 `deployTimestamp: ""` 필드와 `deployment.yaml`에 해당 Pod annotation이 이미 구현되어 있다. ArgoCD ApplicationSet은 `syncPolicy.automated` (prune + selfHeal)으로 설정되어 있어, Git 상태와 클러스터가 다르면 자동 동기화한다.

현재 문제: `main` 브랜치에 코드 변경이 push되어도 Helm values 파일이 변경되지 않으면 ArgoCD는 "이미 동기화됨"으로 판단하여 재배포를 하지 않는다. `initContainer`가 매번 `git clone`으로 최신 코드를 받아오지만, **Pod가 재시작되지 않으면** 새 코드는 실행되지 않는다.

## Goals / Non-Goals

**Goals:**
- `main` push 시 `deployTimestamp`를 자동 갱신하여 ArgoCD가 Deployment 변경을 감지하고 Pod를 재배포
- 워크플로우는 단순하고 외부 시크릿 의존성 없이 동작

**Non-Goals:**
- Docker 이미지 빌드/푸시 파이프라인 (현재 아키텍처는 `git clone` 방식)
- 스테이징/프로덕션 환경 분리 (단일 환경)
- PR 검증 워크플로우 (별도 change로 관리)

## Decisions

### Decision 1: `deployTimestamp` 갱신 방식

**선택:** GitHub Actions에서 `sed` 또는 `yq`로 `values.yaml`의 `deployTimestamp` 값을 현재 UTC 시각으로 교체 후 `git commit && git push`

**대안 고려:**
- **ArgoCD Image Updater**: 이미지 태그 기반 트리거이므로 `git clone` 방식과 맞지 않음
- **ArgoCD Webhook**: push 이벤트를 받아도 Helm values가 동일하면 실제 Deployment는 변경되지 않음 — Pod 재시작 불가
- **Force sync API 호출**: ArgoCD API 토큰 관리가 필요하고 복잡도 증가

**결론:** `deployTimestamp` 방식이 이미 코드베이스에 설계된 패턴이므로 이를 완성하는 것이 가장 자연스럽다.

### Decision 2: 타임스탬프 형식

**선택:** `$(date -u +%Y-%m-%dT%H:%M:%SZ)` — ISO 8601 UTC

**이유:** YAML 문자열로 안전하고, 사람이 읽기 쉬우며, 변경될 때마다 고유값 보장.

### Decision 3: GitHub Actions 권한

**선택:** `contents: write` 권한만 사용 (기본 `GITHUB_TOKEN` 활용)

**이유:** 외부 시크릿 없이 동작. ArgoCD가 동일 저장소를 감시하므로 `git push`만으로 트리거 가능.

### Decision 4: 워크플로우 트리거 범위

**선택:** `push: branches: [main]`에서 `deployment/helm/**` 경로는 제외

**이유:** CI가 `values.yaml`을 수정하고 push하면 다시 워크플로우가 트리거되는 무한루프 방지. `paths-ignore: ['deployment/helm/values.yaml']` 또는 커밋 메시지 `[skip ci]` 중 `paths-ignore` 방식이 더 명시적.

## Risks / Trade-offs

- **[Risk] CI 루프**: 워크플로우가 values.yaml을 push → 다시 워크플로우 트리거 가능  
  → **Mitigation**: `paths-ignore: ['deployment/helm/values.yaml']`로 해당 파일 변경은 트리거 제외

- **[Risk] 동시 push 충돌**: 여러 커밋이 짧은 시간에 push될 경우 `git push` 실패 가능  
  → **Mitigation**: `git pull --rebase` 후 push, 실패 시 워크플로우 재시도 허용

- **[Trade-off] git blame 오염**: CI 봇 커밋이 `git log`에 추가됨  
  → 허용 가능 수준. 커밋 메시지에 `[ci]` 접두어로 구분.

## Migration Plan

1. `.github/workflows/deploy.yml` 파일 생성 및 push
2. 다음 `main` push 시 워크플로우 자동 실행 확인
3. ArgoCD UI에서 `investment-auto` 앱이 `OutOfSync` → `Synced`로 전환되는지 확인
4. Pod가 재시작되어 최신 코드(`git clone`)로 구동되는지 확인

**Rollback**: 워크플로우 파일 삭제 또는 비활성화. `deployTimestamp` 수동 관리로 회귀.
