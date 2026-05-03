## ADDED Requirements

### Requirement: 대시보드 UI 버전 표시
웹 대시보드(`portfolio.html`)는 페이지 하단 footer 영역에 현재 앱 버전을 표시해야 한다. 버전 값은 페이지 로드 시 `GET /api/version`을 JavaScript로 호출하여 동적으로 주입한다.

#### Scenario: 페이지 로드 시 버전 표시
- **WHEN** 사용자가 대시보드 페이지(`/`)를 로드하면
- **THEN** 페이지 하단 footer에 현재 앱 버전 텍스트(예: `v1.0.0`)가 표시되어야 한다

#### Scenario: API 호출 실패 시 fallback
- **WHEN** `/api/version` 호출이 실패하면
- **THEN** 버전 표시 영역은 빈 값 또는 `-`로 표시되어야 하며, 페이지의 다른 기능에 영향을 줘서는 안 된다
