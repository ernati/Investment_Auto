## Context

현재 Investment_Auto 웹 대시보드(`Scripts/modules/web_server.py`)는 `/health`, `/api/portfolio` 등의 엔드포인트를 제공하지만, 앱 버전을 외부에서 조회할 수 있는 방법이 없다. 버전 정보는 `Scripts/__init__.py`에 `__version__ = '1.0.0'`으로 정의되어 있으며, Helm `Chart.yaml`의 `appVersion`과 동기화되어 있다. 운영팀은 배포 후 현재 실행 중인 버전을 웹 인터페이스나 API 호출만으로 빠르게 검증해야 한다.

## Goals / Non-Goals

**Goals:**
- `GET /api/version` 엔드포인트 추가 — `Scripts/__init__.__version__`을 단일 소스로 사용하여 버전 정보를 JSON으로 반환
- 웹 대시보드(`portfolio.html`) UI에 버전 텍스트 표시
- 별도의 외부 의존성 추가 없이 기존 Flask 라우팅 패턴 그대로 활용

**Non-Goals:**
- 빌드 타임 메타데이터(commit hash, build date) 자동 주입 — 현재 CI/CD 파이프라인 변경 불필요
- 버전 기반 API 게이트웨이 라우팅
- 인증/인가 적용 (`/health`와 동일하게 공개 엔드포인트)

## Decisions

### 1. 버전 소스: `Scripts/__init__.__version__` 직접 임포트

`Scripts/__init__.py`에 이미 정의된 `__version__` 변수를 `web_server.py`에서 직접 임포트하여 사용한다.

**대안 검토:**
- `deployment/helm/Chart.yaml`의 `appVersion` 파싱 → 파일 I/O 필요, 런타임 오류 가능성 있음. 탈락.
- 환경 변수(`APP_VERSION`) 주입 → Helm/Docker 설정 변경 필요, 과도한 복잡성. 탈락.

### 2. API 응답 구조: 최소한의 JSON 필드

```json
{
  "version": "1.0.0",
  "environment": "production"
}
```

`environment` 필드는 기존 `config.json`의 `environment` 값을 활용한다.

**대안 검토:**
- commit hash, build timestamp 포함 → CI/CD 파이프라인 변경 필요. 이 변경 범위 밖. 탈락.

### 3. UI 표시 위치: 대시보드 하단 footer 영역

기존 `portfolio.html`의 하단에 작은 텍스트로 버전을 표시한다. 헤더보다 시각적으로 덜 방해되며, footer는 이미 정보 표시 관행상 적절한 위치다.

버전 값은 페이지 로드 시 `/api/version`을 호출하여 JavaScript로 주입한다 (서버사이드 템플릿 변수 대신). 기존 API 호출 패턴(`/api/portfolio`)과 일관성을 유지한다.

## Risks / Trade-offs

- **[Risk]** `Scripts/__init__.py`와 Helm `appVersion`이 수동으로 관리되어 불일치 가능성 → CI/CD에서 두 값을 동기화하는 별도 검증 단계 추가 권장 (이 변경 범위 밖)
- **[Trade-off]** `/api/version`을 공개 엔드포인트로 노출 → 버전 정보 노출이 보안 위협이 될 수 있으나, 내부 운영 도구 성격상 수용 가능
- **[Trade-off]** JavaScript fetch 방식은 JS 비활성화 환경에서 버전이 표시되지 않음 → 운영 모니터링 목적이므로 영향 없음
