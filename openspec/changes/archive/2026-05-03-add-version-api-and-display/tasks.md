## 1. API 엔드포인트 구현

- [x] 1.1 `Scripts/modules/web_server.py`에서 `Scripts.__version__` 임포트 추가
- [x] 1.2 `_setup_routes()`에 `GET /api/version` 라우트 등록
- [x] 1.3 `/api/version` 핸들러 구현 — `{"version": __version__, "environment": self.env}` JSON 반환

## 2. 웹 대시보드 UI 수정

- [x] 2.1 `Scripts/templates/portfolio.html` 하단에 footer 영역 추가 (버전 표시용 요소)
- [x] 2.2 페이지 로드 시 `GET /api/version`을 fetch하여 버전 텍스트를 footer에 주입하는 JavaScript 추가
- [x] 2.3 `/api/version` 호출 실패 시 버전 표시를 `-`로 fallback 처리

## 3. 검증

- [x] 3.1 `GET /api/version` 호출 시 `{"version": "...", "environment": "..."}` 응답 확인
- [x] 3.2 대시보드 페이지 로드 후 footer에 버전 텍스트가 표시되는지 확인
