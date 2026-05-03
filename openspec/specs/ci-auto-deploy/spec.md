# Spec: ci-auto-deploy

## Purpose

`main` 브랜치에 코드 변경이 push될 때 Helm `values.yaml`의 `deployTimestamp`를 자동 갱신하여 ArgoCD가 Pod 재배포를 감지하도록 하는 CI 자동 배포 파이프라인을 정의한다.

---

## Requirements

### Requirement: main 브랜치 push 시 Helm values 자동 갱신
시스템은 `main` 브랜치에 코드 변경이 push될 때 `deployment/helm/values.yaml`의 `deployTimestamp` 값을 현재 UTC 시각으로 자동 갱신하고 커밋·push하여 ArgoCD가 Deployment 변경을 감지하고 Pod를 재배포하도록 SHALL 트리거해야 한다.

단, `deployment/helm/values.yaml` 파일 자체의 변경은 이 워크플로우를 트리거하지 않아야 한다 (무한루프 방지).

#### Scenario: 코드 변경 push 시 자동 배포 트리거
- **WHEN** `main` 브랜치에 `deployment/helm/values.yaml` 이외의 파일 변경이 push되면
- **THEN** GitHub Actions 워크플로우가 실행되어 `deployTimestamp`가 현재 UTC 시각(ISO 8601)으로 갱신된 커밋이 `main`에 push되어야 한다

#### Scenario: values.yaml 변경은 워크플로우를 트리거하지 않음
- **WHEN** `deployment/helm/values.yaml` 파일만 변경되어 `main`에 push되면
- **THEN** GitHub Actions 워크플로우가 실행되지 않아야 한다 (무한루프 방지)

#### Scenario: 타임스탬프 형식
- **WHEN** 워크플로우가 `deployTimestamp`를 갱신하면
- **THEN** 값은 `YYYY-MM-DDTHH:MM:SSZ` 형식의 UTC 시각 문자열이어야 한다

### Requirement: 외부 시크릿 없이 동작
CI 파이프라인은 GitHub 저장소 기본 `GITHUB_TOKEN`만을 사용하여 동작해야 하며 추가적인 외부 시크릿이나 서비스 계정을 필요로 해서는 안 된다.

#### Scenario: 기본 토큰으로 push 성공
- **WHEN** 워크플로우가 `GITHUB_TOKEN`을 사용하여 `git push`를 실행하면
- **THEN** `main` 브랜치에 커밋이 성공적으로 push되어야 한다
