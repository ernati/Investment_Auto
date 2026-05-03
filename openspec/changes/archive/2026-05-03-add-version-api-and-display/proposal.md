## Why

운영 환경에 배포된 앱의 버전을 외부에서 쉽게 확인할 방법이 없어, 배포 성공 여부나 현재 실행 중인 버전을 검증하려면 서버/컨테이너에 직접 접속해야 했다. API와 웹 대시보드를 통해 버전 정보를 노출하면 배포 확인 및 트러블슈팅이 빠르고 간편해진다.

## What Changes

- `GET /api/version` 엔드포인트 추가: 앱 버전, 환경(environment) 정보를 JSON으로 반환
- 웹 대시보드(`portfolio.html`)에 앱 버전 표시 영역 추가 (페이지 하단 또는 헤더 영역)
- `Scripts/__init__.py`의 `__version__` 값을 버전 정보의 단일 소스(source of truth)로 사용

## Capabilities

### New Capabilities
- `version-api`: `GET /api/version` REST 엔드포인트 및 버전 정보 응답 스펙

### Modified Capabilities
- `web-dashboard`: 대시보드 UI에 버전 정보 표시 영역 추가 (새로운 UI 요구사항)

## Impact

- `Scripts/modules/web_server.py`: 새 라우트(`/api/version`) 등록
- `Scripts/templates/portfolio.html`: 버전 표시 UI 추가
- `Scripts/__init__.py`: 기존 `__version__` 변수 활용 (변경 없음)
