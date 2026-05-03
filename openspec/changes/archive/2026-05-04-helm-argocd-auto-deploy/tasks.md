## 1. GitHub Actions 워크플로우 생성

- [x] 1.1 `.github/workflows/deploy.yml` 파일 생성
- [x] 1.2 트리거 설정: `push: branches: [main]`, `paths-ignore: ['deployment/helm/values.yaml']`
- [x] 1.3 `contents: write` 권한 설정
- [x] 1.4 `deployTimestamp`를 현재 UTC 시각으로 갱신하는 `sed` 명령 작성
- [x] 1.5 git 사용자 설정 (`github-actions[bot]`) 및 커밋·push 단계 작성

## 2. 검증

- [x] 2.1 `main`에 테스트 커밋 push 후 GitHub Actions 워크플로우 실행 확인
- [x] 2.2 `deployment/helm/values.yaml`의 `deployTimestamp`가 갱신된 커밋이 생성됐는지 확인
- [x] 2.3 ArgoCD UI에서 `investment-auto` 앱이 `OutOfSync` → `Synced`로 전환되는지 확인
- [x] 2.4 Pod가 재시작되어 최신 코드로 구동되는지 확인
