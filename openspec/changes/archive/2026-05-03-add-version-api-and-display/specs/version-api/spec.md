## ADDED Requirements

### Requirement: 버전 정보 조회 API
시스템은 `GET /api/version` 엔드포인트를 통해 현재 앱 버전 및 환경 정보를 JSON으로 반환해야 한다. 버전 값의 단일 소스는 `Scripts/__init__.__version__`이며, 별도의 외부 설정 파일이나 환경 변수를 사용해서는 안 된다.

응답 형식:
```json
{
  "version": "1.0.0",
  "environment": "production"
}
```

- `version`: `Scripts/__init__.__version__` 값
- `environment`: 서버 초기화 시 주입된 `env` 파라미터 값

#### Scenario: 버전 조회 성공
- **WHEN** 클라이언트가 `GET /api/version`을 호출하면
- **THEN** 시스템은 HTTP 200과 함께 `version`, `environment` 필드를 포함한 JSON을 반환해야 한다

#### Scenario: 인증 없이 접근 가능
- **WHEN** 인증 헤더 없이 `GET /api/version`을 호출하면
- **THEN** 시스템은 HTTP 200으로 정상 응답해야 한다 (공개 엔드포인트)
