## Why

코드가 `main` 브랜치에 push되어도 ArgoCD가 재배포를 트리거하는 CI 파이프라인이 없다. `values.yaml`에 `deployTimestamp` 필드와 `deployment.yaml`에 해당 annotation이 이미 준비되어 있지만, 이 값을 자동으로 갱신하는 GitHub Actions 워크플로우가 존재하지 않아 배포 자동화가 불완전한 상태다.

## What Changes

- `.github/workflows/deploy.yml` 생성: `main` 브랜치에 push 발생 시 `deployment/helm/values.yaml`의 `deployTimestamp`를 현재 UTC 시각(ISO 8601)으로 자동 갱신하고 커밋·push하여 ArgoCD의 자동 동기화(`syncPolicy.automated`)를 트리거
- `deployment/helm/values.yaml`의 `deployTimestamp` 기본값을 빈 문자열(`""`)에서 명시적 플레이스홀더로 변경하여 CI 의도를 문서화

## Capabilities

### New Capabilities
- `ci-auto-deploy`: `main` push 시 GitHub Actions가 Helm values의 `deployTimestamp`를 갱신하여 ArgoCD 재배포를 자동으로 트리거하는 CI 파이프라인

### Modified Capabilities
- `web-dashboard`: 변경 없음 (배포 인프라 변경만)

## Impact

- `.github/workflows/deploy.yml`: 신규 파일
- `deployment/helm/values.yaml`: `deployTimestamp` 주석 보강
- ArgoCD ApplicationSet은 수정 불필요 (`syncPolicy.automated`가 이미 활성화됨)
- GitHub 저장소에 Actions 권한(`contents: write`)이 필요
