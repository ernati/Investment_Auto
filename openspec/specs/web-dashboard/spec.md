# Spec: Web Dashboard

**Capability:** `web-dashboard`  
**Source:** `Scripts/modules/web_server.py`, `Scripts/templates/portfolio.html`  
**Last synced:** 2026-04-18

---

## Purpose

리밸런싱 스케줄러와 함께 백그라운드에서 실행되는 Flask 웹 서버. 포트폴리오 현황 대시보드와 DB 이력 조회 REST API를 제공한다. 리밸런싱 실행과 완전히 독립적으로 동작한다.

---

## Interface

```python
PortfolioWebServer(
    port: int = 5000,
    host: str = "127.0.0.1",    # 컨테이너 환경이면 "0.0.0.0"
    env: str = "demo",
    unified_fetcher: Optional[UnifiedPortfolioFetcher] = None
)

server.start()      # daemon thread로 실행, 반환 즉시
server.stop()
server.is_running() -> bool
```

**스레드 모델:** `start()`는 Flask를 daemon thread에서 실행. 메인 프로세스 종료 시 자동 종료.  
`stop()`은 `self.running = False`만 설정 — Flask WSGI 서버를 강제 종료하지는 않음.

---

## REST API

### `GET /`
포트폴리오 대시보드 HTML 페이지.  
템플릿: `Scripts/templates/portfolio.html`

---

### `GET /health`

```json
{
  "status": "healthy",
  "timestamp": "2026-04-18T09:00:00",
  "environment": "real",
  "api_status": "connected",   // "disconnected" if KISAuth 초기화 실패
  "db_status": "connected"     // "disconnected" if DatabaseManager 초기화 실패
}
```

---

### `GET /api/portfolio`

포트폴리오 현황. **30초 캐시** 적용.

`unified_fetcher` 있을 때 (정상 경로):
```json
{
  "timestamp": "2026-04-18T09:00:00",
  "environment": "real",
  "account": "12345678-01",
  "summary": {
    "total_assets": 100000000,
    "cash": 5000000,
    "kis_cash": 4000000,
    "upbit_krw": 1000000,
    "cash_ratio": 5.0,
    "total_stock_value": 80000000,
    "stock_ratio": 80.0,
    "total_bond_value": 5000000,
    "bond_ratio": 5.0,
    "total_crypto_value": 10000000,
    "crypto_ratio": 10.0
  },
  "positions": [
    {
      "ticker": "005930",
      "name": "005930",
      "category": "stocks",
      "quantity": 100,
      "current_price": 75000,
      "market_value": 7500000,
      "ratio": 7.5
    }
  ],
  "balance": {
    "total_cash": 5000000,
    "kis_cash": 4000000,
    "upbit_krw": 1000000
  }
}
```

`unified_fetcher` 없을 때 (KIS 전용 fallback):
- `summary`에 `kis_cash`, `upbit_krw`, `bond_ratio`, `crypto_ratio` 없음
- `positions`에 `category` 없음

오류 시:
```json
{ "error": "error message", "timestamp": "...", "environment": "..." }
```

HTTP 500 반환.

---

### `GET /api/db/trading-history`

**DB 필수.** DB 없으면 HTTP 500.

Query params:
| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| `portfolio_id` | `"all"` | `"all"` = 전체 |
| `environment` | `"all"` | `"all"` = 전체 |
| `limit` | `50` | 최대 조회 수 |
| `offset` | `0` | 페이지 오프셋 |

```json
{
  "data": [...],
  "total": 50,
  "limit": 50,
  "offset": 0
}
```

---

### `GET /api/db/rebalancing-logs`

**DB 필수.** Query params: `portfolio_id`, `environment`, `limit`(30), `offset`(0).

---

### `GET /api/db/portfolio-snapshots`

**DB 필수.** Query params: `portfolio_id`, `environment`, `limit`(30), `offset`(0).

---

### `GET /api/db/system-logs`

**DB 필수.** `system_logs` 테이블 직접 쿼리.

Query params:
| 파라미터 | 기본값 | 필터 방식 |
|---------|--------|----------|
| `level` | `""` | 정확히 일치 |
| `module` | `""` | ILIKE `%module%` |
| `environment` | 서버 `env` | 정확히 일치 |
| `limit` | `50` | — |
| `offset` | `0` | — |

---

## Data Source Priority

```
/api/portfolio 호출 시:

  캐시 유효 (30초 이내)?
  └─ YES → 캐시 반환

  unified_fetcher 있음?
  ├─ YES → unified_fetcher.get_portfolio_snapshot() 호출
  │          (KIS holdings API + Upbit API)
  └─ NO  → portfolio_fetcher (KIS 전용) 호출
```

**주의:** `unified_fetcher.get_portfolio_snapshot()`은 `fetch_unified_portfolio_snapshot()`과 다른 경로. KIS holdings를 별도 API로 조회하며 채권 분류가 미구현(`bonds: []`).

---

## Cache

- 캐시 유효기간: **30초** (하드코딩)
- 캐시 무효화: 시간 기반만 지원, 강제 갱신 API 없음
- 캐시 저장 위치: 인스턴스 변수 (`_portfolio_cache`, `_last_update`)

---

## Initialization Behavior

```
__init__:
  KISAuth 초기화 실패 → self.kis_auth = None (경고 로그, 예외 없음)
  DatabaseManager 초기화 실패 → self.db_manager = None (경고 로그, 예외 없음)

결과:
  KISAuth = None → /api/portfolio fallback 경로 실패, "KIS API not available" 반환
  db_manager = None → 모든 /api/db/* 엔드포인트 HTTP 500 반환
```

웹 서버 자체가 초기화 실패해도 `portfolio_rebalancing.py`는 계속 동작.

---

## Dependencies

```
PortfolioWebServer
  ├── UnifiedPortfolioFetcher  (주입, optional)
  ├── KISAuth                  (자체 생성, config.json에서 읽음)
  ├── KISPortfolioFetcher      (KIS 전용 fallback용)
  └── DatabaseManager          (DB API용, optional)
```

**주의:** `PortfolioWebServer`는 `KISAuth`를 내부에서 별도로 생성한다 — `portfolio_rebalancing.py`의 `KISAuth`와 다른 인스턴스.

---

## Invariants

1. 리밸런싱 루프와 공유 상태: `UnifiedPortfolioFetcher` 참조만 공유 (KISAuth는 별도 인스턴스)
2. Flask는 `threaded=True`로 실행 — 동시 요청 처리 가능
3. `/api/db/*` 엔드포인트는 DB 없으면 항상 HTTP 500 반환 (빈 배열 아님)

---

## Requirements

### Requirement: 대시보드 UI 버전 표시
웹 대시보드(`portfolio.html`)는 페이지 하단 footer 영역에 현재 앱 버전을 표시해야 한다. 버전 값은 페이지 로드 시 `GET /api/version`을 JavaScript로 호출하여 동적으로 주입한다.

#### Scenario: 페이지 로드 시 버전 표시
- **WHEN** 사용자가 대시보드 페이지(`/`)를 로드하면
- **THEN** 페이지 하단 footer에 현재 앱 버전 텍스트(예: `v1.0.0`)가 표시되어야 한다

#### Scenario: API 호출 실패 시 fallback
- **WHEN** `/api/version` 호출이 실패하면
- **THEN** 버전 표시 영역은 빈 값 또는 `-`로 표시되어야 하며, 페이지의 다른 기능에 영향을 줘서는 안 된다

---

## Known Issues

- `stop()`이 Flask 서버를 실제로 종료하지 않음 — `self.running = False`만 설정
- `unified_fetcher.get_portfolio_snapshot()`의 채권(`bonds: []`) 미구현
- 캐시 강제 갱신 엔드포인트 없음
- `system_logs` 테이블은 DB 스키마에서 수동 생성 필요 (현재 앱이 자동 생성하지 않음)
