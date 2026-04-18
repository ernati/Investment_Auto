# Spec: Portfolio Rebalancing System

**Capability:** `portfolio-rebalancing`  
**Source:** `Scripts/apps/portfolio_rebalancing.py`  
**Last synced:** 2026-04-18

---

## Purpose

KIS(한국투자증권) 국내주식·채권·해외주식과 Upbit 비트코인을 하나의 포트폴리오로 통합 관리하는 자동 리밸런싱 시스템. 설정된 목표 비중에서 이탈이 감지될 때, 또는 지정 일정에 따라 자동으로 매매 주문을 실행한다.

---

## System Boundaries

이 시스템이 **하는 것**:
- 복수 브로커 계좌를 단일 포트폴리오로 통합 조회
- 목표 비중 대비 현재 비중 편차 계산 및 리밸런싱 필요 여부 판단
- 매매 주문 생성 및 실행 (국내/해외/암호화폐)
- 실행 이력 DB 저장 (옵션)
- 포트폴리오 현황 웹 대시보드 제공 (옵션)

이 시스템이 **하지 않는 것**:
- 종목 선정 (목표 비중은 설정 파일로 외부 주입)
- 세금·수수료 최적화 계산
- 실시간 시세 스트리밍 (API 폴링 방식)
- 복수 포트폴리오 동시 관리

---

## Entry Points

### CLI

```
python Scripts/apps/portfolio_rebalancing.py [options]

Options:
  --mode {once,schedule}     once=단회 실행, schedule=무한 루프 (default: once)
  --interval INT             schedule 모드 체크 주기(초) (default: 60)
  --validate-only            설정 검증만 하고 종료
  --skip-schedule-check      스케줄러 시간 체크 무시하고 즉시 실행
  --demo                     모의투자 환경 사용
  --disable-web              웹 서버 비활성화
  --web-port INT             웹 서버 포트 (default: 5000)
  --web-host STR             웹 서버 호스트 (default: 127.0.0.1)
  --db-mode                  PostgreSQL DB 저장 활성화
```

### Programmatic

```python
app = PortfolioRebalancingApp(
    skip_schedule_check=False,
    env="real" | "demo",
    enable_web=True,
    web_port=5000,
    web_host="127.0.0.1",
    db_enabled=False,
)
app.run_once()       # 단회 실행, returns bool
app.run_scheduler()  # 무한 루프
```

---

## Initialization Sequence

순서가 중요하다. 의존성 역순으로 실패한다.

```
1. PortfolioConfigLoader.load()     ← config_basic.json + config_advanced.json
2. ConfigLoader.load()              ← config.json (KIS API 키)
3. ConfigValidator.validate()       ← 실패 시 RuntimeError → 즉시 종료
4. KISAuth 초기화                   ← env별 appkey/appsecret/account
5. UpbitClient 초기화               ← env별 access/secret key
6. UnifiedPortfolioFetcher 초기화   ← KISAuth + UpbitClient
7. PortfolioScheduler 초기화
8. RebalancingEngine 초기화
9. OrderExecutor 초기화             ← KISAuth + UpbitClient
10. PortfolioWebServer 초기화 (옵션) ← 실패해도 앱은 계속 동작
11. DatabaseManager 초기화 (옵션)    ← 실패해도 앱은 계속 동작
```

**불변 조건:** 3번(설정 검증) 실패 시 이후 단계 진행 불가.  
**허용 실패:** 10번(웹 서버), 11번(DB)은 실패해도 리밸런싱 본 기능은 동작.

---

## Rebalancing Cycle (run_once)

```
run_once()
  │
  ├─ [skip_schedule_check=False] Scheduler.is_execution_time()?
  │     └─ NO → return False
  │
  ├─ [market_hours_enabled=True] MarketHours.get_market_status()?
  │     └─ closed → return False
  │
  ├─ UnifiedPortfolioFetcher.fetch_unified_portfolio_snapshot()
  │     └─ → PortfolioSnapshot
  │
  ├─ RebalancingEngine.create_rebalance_plan(snapshot)
  │     └─ → RebalancePlan
  │         └─ plan.should_rebalance = False → return False
  │
  ├─ RebalancingEngine.apply_guardrails(plan)
  │     └─ → adjusted_plan
  │         └─ total_orders = 0 → return False
  │
  ├─ OrderExecutor.execute_plan(adjusted_plan)
  │     └─ → ExecutionResult
  │
  ├─ [succeeded] Scheduler.record_execution()
  │
  └─ [db_enabled] DatabaseManager.save(snapshot, plan, result)
```

**반환값 의미:**
- `True`: 리밸런싱 실행 완료
- `False`: 실행 조건 불충족 또는 주문 없음 (정상 상태)
- Exception: 예상치 못한 오류 (로그 기록 후 `False` 반환)

---

## Module Dependency Map

변경 시 영향 범위를 파악하기 위한 맵.

```
portfolio_rebalancing.py
  ├── config_loader.py          (변경 시 영향: 전체)
  ├── config_validator.py       (변경 시 영향: 시작 시퀀스)
  ├── kis_auth.py               (변경 시 영향: order_executor, web_server, kis_*)
  ├── unified_portfolio_fetcher.py
  │     ├── kis_portfolio_fetcher.py
  │     │     └── kis_api_client.py
  │     └── upbit_api_client.py
  ├── rebalancing_engine.py     (변경 시 영향: order_executor 입력 계약)
  │     └── portfolio_models.py (변경 시 영향: 전체 데이터 흐름)
  ├── order_executor.py
  │     ├── kis_trading.py
  │     ├── kis_overseas_trading.py
  │     ├── upbit_api_client.py
  │     └── market_hours.py
  ├── scheduler.py
  ├── market_hours.py
  ├── web_server.py             (독립적, 장애 허용)
  └── db_manager.py             (독립적, 장애 허용)
```

**핵심 의존 모듈:** `portfolio_models.py` — 이 파일의 데이터클래스가 변경되면 전체 파이프라인에 영향.

---

## Environment Modes

| Mode | env 값 | KIS API | Upbit API | 실제 주문 |
|------|--------|---------|-----------|----------|
| 실전투자 | `"real"` | 실전 endpoint | 실전 키 | O |
| 모의투자 | `"demo"` | 모의 endpoint | 모의 키 | X (시뮬레이션) |

`--demo` 플래그 → `env="demo"` → 모든 하위 모듈에 전달됨.  
env 값은 `KISAuth`, `UpbitClient`, `OrderExecutor`, `WebServer` 생성자에 명시적으로 주입된다.

---

## Optional Features

### Web Server

- Flask 기반, 별도 daemon thread에서 실행
- `enable_web=False` 또는 초기화 실패 시 완전히 비활성화
- 리밸런싱 루프와 독립적으로 동작 (공유 상태: `UnifiedPortfolioFetcher` 참조)
- 상세 스펙: `specs/web-dashboard/spec.md`

### Database Logging

- `db_enabled=True` + `--db-mode` 플래그로 활성화
- PostgreSQL 전용 (`psycopg2-binary` 필요)
- 저장 항목: `PortfolioSnapshot`, `TradingHistory`, `RebalancingLog`
- DB 장애 시 리밸런싱 실행은 계속 진행 (저장만 스킵)
- `DB_AVAILABLE = False` 상태에서 `db_enabled=True`이면 `RuntimeError` (명시적 실패)

---

## Invariants (불변 조건)

1. **매도 먼저, 매수 나중** — `OrderExecutor`는 항상 sell 주문을 buy보다 먼저 실행한다. 현금 확보 전 매수 불가.
2. **설정 검증 필수** — `ConfigValidator` 통과 없이 리밸런싱 실행 불가.
3. **장 마감 시 해외 주문 스킵** — 해외 거래소 마감 상태에서는 해당 종목 주문을 오류 없이 스킵.
4. **env는 생성 시 고정** — 실행 중 환경(real/demo) 전환 불가. 재시작 필요.
5. **목표 비중 합계 = 1.0** — `ConfigValidator`에서 강제. 위반 시 시작 불가.

---

## Known Limitations

- 장중 가격 변동으로 인해 `fetch` → `execute` 사이 슬리피지 발생 가능
- 해외 주식은 지정가 주문(`order_division="00"`)만 지원 — 미체결 주문 관리 없음
- Bitcoin 포지션은 `quantity=1` 컨벤션 사용 (실제 BTC 수량이 아님) — `evaluation`이 실제 KRW 평가액
- 단일 프로세스 단일 포트폴리오만 지원
