# Portfolio Rebalancing System - 완전 가이드

## 📋 목차
1. [시스템 개요](#시스템-개요)
2. [구조 및 모듈](#구조-및-모듈)
3. [빠른 시작](#빠른-시작)
4. [설정 가이드](#설정-가이드)
5. [사용 방법](#사용-방법)
6. [트러블슈팅](#트러블슈팅)
7. [개발 리소스](#개발-리소스)

## 시스템 개요

### 목적
KIS Open API를 활용하여 **포트폴리오의 목표 비중을 자동으로 유지**하는 시스템입니다.

### 주요 특징
✅ **자동 리밸런싱**: 목표 비중 유지 자동화  
✅ **유연한 스케줄**: Hourly, Daily, Calendar rules 지원  
✅ **위험 제어**: 가드레일(guardrails)로 위험 관리  
✅ **Dry-run 모드**: 개발 및 테스트 환경 지원  
✅ **실전 모드**: 실제 주문 실행 가능  
✅ **설정 기반**: JSON 설정으로 모든 파라미터 제어  

### 작동 원리

```
1️⃣ 설정 로드
   Config/config_basic.json + config_advanced.json
   ↓
2️⃣ 포트폴리오 조회
   KIS API로 현금, 보유종목, 가격 조회
   ↓
3️⃣ 리밸런싱 판단
   현재 비중 vs 목표 비중 비교
   BAND, CALENDAR, HYBRID 모드별 판단
   ↓
4️⃣ 주문 계획 수립
   매도할 종목, 매수할 종목 결정
   ↓
5️⃣ 위험 검증
   가드레일 통과 여부 확인
   ↓
6️⃣ 주문 실행 (또는 시뮬레이션)
   매도 → 매수 순서로 실행
```

## 구조 및 모듈

### 프로젝트 구조
```
Investment_Auto/
├── Config/                           # 설정 파일
│   ├── config_basic.json            # 기본 설정 (필수)
│   ├── config_advanced.json         # 고급 설정 (선택)
│   └── config.json                  # 레거시
│
├── Scripts/
│   ├── apps/                        # 애플리케이션
│   │   └── portfolio_rebalancing.py # 메인 앱
│   │
│   └── modules/                     # 핵심 모듈들
│       ├── config_loader.py         # 설정 로드/관리
│       ├── portfolio_models.py      # 데이터 모델
│       ├── kis_portfolio_fetcher.py # 포트폴리오 조회
│       ├── scheduler.py             # 스케줄링
│       ├── rebalancing_engine.py    # 리밸런싱 로직
│       ├── order_executor.py        # 주문 실행
│       ├── config_validator.py      # 설정 검증
│       ├── kis_auth.py              # KIS 인증 (기존)
│       └── __pycache__/
│
└── docs/                            # 문서
    ├── Investment_portfolio.md      # 설계서
    ├── portfolio_rebalancing.md     # 메인 앱 문서
    ├── portfolio_config_loader.md   # 설정 로더 문서
    ├── portfolio_models.md          # 데이터 모델 문서
    ├── kis_portfolio_fetcher.md     # 포트폴리오 조회 문서
    ├── scheduler.md                 # 스케줄러 문서
    ├── rebalancing_engine.md        # 리밸런싱 엔진 문서
    ├── order_executor.md            # 주문 실행 문서
    ├── config_validator.md          # 설정 검증 문서
    └── (기존 문서들)
```

### 모듈 관계도

```
portfolio_rebalancing.py (메인 앱)
          │
          ├─→ config_loader.py (설정 관리)
          │   ├─ config_basic.json
          │   └─ config_advanced.json
          │
          ├─→ config_validator.py (설정 검증)
          │   └─ 검증 규칙 적용
          │
          ├─→ kis_auth.py (KIS 인증)
          │   └─ 토큰 발급/갱신
          │
          ├─→ kis_portfolio_fetcher.py (포트폴리오 조회)
          │   ├─ KIS API 호출
          │   ├─ portfolio_models.py (PortfolioSnapshot 생성)
          │   └─ kis_auth.py (인증 사용)
          │
          ├─→ scheduler.py (스케줄 판단)
          │   └─ config_loader.py (스케줄 설정 읽기)
          │
          ├─→ rebalancing_engine.py (리밸런싱 판단/계획)
          │   ├─ config_loader.py (설정 읽기)
          │   └─ portfolio_models.py (RebalancePlan 생성)
          │
          └─→ order_executor.py (주문 실행)
              ├─ KIS API 호출
              ├─ kis_auth.py (인증 사용)
              └─ portfolio_models.py (ExecutionResult 생성)
```

## 빠른 시작

### Step 1: 설정 준비
```bash
# Config 디렉토리 생성 및 설정 파일 작성
# (이미 config_basic.json, config_advanced.json이 있으면 OK)
```

### Step 2: 설정 검증
```bash
python Scripts/apps/portfolio_rebalancing.py --validate-only
```

✅ 모든 검증이 통과하면 진행

### Step 3: Dry-run으로 테스트
```bash
# config_basic.json에서 dry_run: true 인지 확인
python Scripts/apps/portfolio_rebalancing.py --mode once
```

로그에서 리밸런싱 계획 및 시뮬레이션된 주문 확인

### Step 4: 스케줄러 테스트 (선택)
```bash
python Scripts/apps/portfolio_rebalancing.py --mode schedule --interval 60
```

60초마다 실행 여부를 판단하며 실행

(Ctrl+C로 중단)

### Step 5: 실전 모드 전환 (신중하게)
```bash
# 1. config_basic.json에서 dry_run: false로 변경
# 2. config_advanced.json에서 broker 정보 확인
# 3. 다시 검증
python Scripts/apps/portfolio_rebalancing.py --validate-only
# 4. 한 번만 실행
python Scripts/apps/portfolio_rebalancing.py --mode once
```

## 설정 가이드

### 최소 필수 설정

#### config_basic.json
```json
{
  "portfolio_id": "portfolio-001",
  "base_currency": "KRW",
  "target_weights": {
    "005930": 0.50,    // 삼성전자 50%
    "000660": 0.30,    // SK하이닉스 30%
    "035420": 0.20     // NAVER 20%
  },
  "rebalance": {
    "mode": "HYBRID",
    "price_source": "last",
    "band": {
      "type": "ABS",
      "value": 0.05
    },
    "schedule": {
      "timezone": "Asia/Seoul",
      "run_times": [],
      "calendar_rules": {
        "hourly": {
          "enabled": true,
          "minute": 0
        }
      }
    }
  },
  "trade": {
    "cash_buffer_ratio": 0.02,
    "min_order_krw": 100000
  },
  "kis": {
    "appkey": "YOUR_APPKEY",
    "appsecret": "YOUR_APPSECRET",
    "account_number": "00000000",
    "product_code": "01",
    "hts_id": ""
  },
  "dry_run": true
}
```

#### config_advanced.json (선택)
```json
{
  "run_limit": {
    "max_runs_per_day": 24
  },
  "order_policy": {
    "order_type": "market"
  },
  "risk_guardrails": {
    "max_turnover_per_run": 0.1,
    "max_orders_per_run": 30,
    "max_single_order_krw": 5000000
  }
}
```

### 주요 설정 항목

| 항목 | 설명 | 기본값 | 필수 |
|------|------|--------|------|
| `portfolio_id` | 포트폴리오 ID | - | ✅ |
| `target_weights` | 목표 비중 | - | ✅ |
| `rebalance/mode` | BAND/CALENDAR/HYBRID | HYBRID | ✅ |
| `rebalance/band/value` | 밴드 크기 | 0.05 (5%) | 조건부 |
| `trade/cash_buffer_ratio` | 현금 보유 비율 | 0.02 (2%) | ✅ |
| `dry_run` | 시뮬레이션 모드 | true | ✅ |
| `run_limit/max_runs_per_day` | 일일 최대 실행 | 999 | O |
| `risk_guardrails/*` | 위험 제어 | - | O |

## 사용 방법

### Command Line Interface

#### 1. 설정 검증만
```bash
python Scripts/apps/portfolio_rebalancing.py --validate-only
```

**Output:**
```
============================================================
Configuration Validation Report
============================================================

✅ All validations passed!
============================================================
```

#### 2. 한 번 실행
```bash
python Scripts/apps/portfolio_rebalancing.py --mode once
```

**Output:**
```
2025-02-08 10:00:05,123 - __main__ - INFO - Starting Portfolio Rebalancing Application
2025-02-08 10:00:05,456 - modules.kis_portfolio_fetcher - INFO - Fetching portfolio...
2025-02-08 10:00:07,789 - modules.rebalancing_engine - INFO - Rebalancing triggered: BAND breach
2025-02-08 10:00:08,012 - modules.order_executor - INFO - [DRY-RUN] Order simulated...
2025-02-08 10:00:08,234 - __main__ - INFO - Plan executed successfully: 3 orders
```

#### 3. 스케줄러로 지속 실행
```bash
# 60초마다 확인
python Scripts/apps/portfolio_rebalancing.py --mode schedule --interval 60

# 30초마다 확인
python Scripts/apps/portfolio_rebalancing.py --mode schedule --interval 30
```

**Output:**
```
(계속 실행되며, 실행 시간마다 로그 출력)
2025-02-08 10:00:00 - ... - Running rebalancing cycle
2025-02-08 10:01:00 - ... - Running rebalancing cycle
...
```

### Python API 사용

#### 기본 사용법
```python
from modules.config_loader import get_portfolio_config
from modules.kis_auth import KISAuth
from modules.kis_portfolio_fetcher import KISPortfolioFetcher
from modules.scheduler import PortfolioScheduler
from modules.rebalancing_engine import RebalancingEngine
from modules.order_executor import OrderExecutor

# 1. 설정 로드
config = get_portfolio_config()

# 2. KIS 인증
kis_auth = KISAuth(
    appkey=config.get_basic("kis/appkey"),
    appsecret=config.get_basic("kis/appsecret"),
    account=config.get_basic("kis/account_number"),
)

# 3. 포트폴리오 조회
fetcher = KISPortfolioFetcher(kis_auth)
snapshot = fetcher.fetch_portfolio_snapshot("portfolio-001")

# 4. 스케줄 확인
scheduler = PortfolioScheduler(config)
if not scheduler.is_execution_time():
    print("Not execution time")
    exit(0)

# 5. 리밸런싱 판단
engine = RebalancingEngine(config)
plan = engine.create_rebalance_plan(snapshot)

if not plan.should_rebalance:
    print(f"No rebalancing needed: {plan.rebalance_reason}")
    exit(0)

# 6. 가드레일 검사
passed, msg = engine.check_guardrails(plan)
if not passed:
    print(f"Guardrail failed: {msg}")
    exit(1)

# 7. 주문 실행
executor = OrderExecutor(config, kis_auth)
result = executor.execute_plan(plan)

if result.succeeded:
    print(f"✅ Execution successful: {len(result.executed_orders)} orders")
else:
    print(f"❌ Execution failed: {result.error_message}")
```

## 트러블슈팅

### Q1: "설정 검증 실패" 메시지가 출력됨
```
Solution:
1. python Scripts/apps/portfolio_rebalancing.py --validate-only 실행
2. 에러 메시지 확인
3. 해당 항목을 config_basic.json에서 수정
   예: "Sum must be 1.0, got 0.95" → target_weights 합계가 0.95
4. 다시 검증
```

### Q2: 리밸런싱이 절대 실행되지 않음
```
Possible Causes:
1. 스케줄 설정이 없음 (hourly.enabled=false AND run_times=[])
   → config_basic.json의 schedule 설정 확인

2. 실행 시간이 아님
   → Scheduler의 next_execution_time() 확인
   → 로그의 timestamp 확인

3. 일일 실행 횟수 초과
   → max_runs_per_day 값 확인
   → log에서 "Daily run limit reached" 메시지 확인

4. Band 조건이 만족되지 않음 (BAND/HYBRID 모드)
   → 현재 비중이 밴드 범위 내
   → 목표 비중 재확인
```

### Q3: KIS API 호출 오류

#### 일반적인 HTTP 에러
```
Error: "API 호출 실패: ..."

Solution:
1. KIS 포털 상태 확인 (openapi.koreainvestment.com)
2. 네트워크 연결 확인
3. 계좌번호 + 상품코드 정확한지 확인
4. 토큰 만료 (자동 갱신되지만, 생김 경우 수동 갱신)
5. API 호출 제한 확인 (심한 경우 일부 API 차단)
```

#### 🆕 개선된 에러 메시지 (2026-02-16 업데이트)
이제 HTTP 500 에러 등이 발생해도 한국투자증권 API의 상세한 에러 메시지를 확인할 수 있습니다:

**기존:**
```
ERROR - HTTP error - 500 Server Error: Internal Server Error
```

**개선 후:**
```
ERROR - KIS API error - [40100000] 모의투자 영업일이 아닙니다. (HTTP 500)
ERROR - Plan execution failed: [40100000] 모의투자 영업일이 아닙니다.
```

**주요 에러 코드와 해결방법:**

| 에러 코드 | 메시지 | 해결방법 |
|-----------|--------|----------|
| `40100000` | 모의투자 영업일이 아닙니다 | 시장 영업시간 확인, 휴장일 피하기 |
| `40040000` | 없는 서비스 코드 입니다 | 종목코드 확인, API 엔드포인트 확인 |
| `40310000` | 조회할 자료가 없습니다 | 계좌 정보 확인, 보유종목 확인 |

### Q4: "주문 실행 실패" 메시지
```
Dry-run 모드인 경우: 정상 (시뮬레이션)
실전 모드인 경우:
1. 주문 가능 현금 확인
2. 종목코드 정확성 확인
3. 수량이 유효한지 확인 (최소 주문수)
4. 로그에서 상세 에러 메시지 확인
```

### Q5: 매수 주문만 실행되고 매도 주문은 실행되지 않음
```
Reason: 내부적으로 매도를 먼저 실행하지만,
        매도할 포지션이 없으면 당연히 실행 안 됨

Check:
1. 보유종목이 초과 상태인가?
2. target_weights에는 종목이 있는가?
3. 새로운 포트폴리오 구성이 목표와 다른가?
```

### Q6: 로그 파일이 너무 커짐
```
Solution:
1. portfolio_rebalancing.log 파일 확인
2. 주기적으로 로테이션 (예: 일주일에 한 번)
   → mv portfolio_rebalancing.log portfolio_rebalancing.log.$(date +%Y%m%d)
3. 또는 logrotate 유틸리티 사용
```

## 개발 리소스

### 모듈별 문서

| 모듈 | 문서 | 용도 |
|------|------|------|
| `config_loader.py` | [portfolio_config_loader.md](./portfolio_config_loader.md) | 설정 로드/관리 |
| `portfolio_models.py` | [portfolio_models.md](./portfolio_models.md) | 데이터 모델 |
| `kis_portfolio_fetcher.py` | [kis_portfolio_fetcher.md](./kis_portfolio_fetcher.md) | 포트폴리오 조회 |
| `scheduler.py` | [scheduler.md](./scheduler.md) | 스케줄 관리 |
| `rebalancing_engine.py` | [rebalancing_engine.md](./rebalancing_engine.md) | 리밸런싱 로직 |
| `order_executor.py` | [order_executor.md](./order_executor.md) | 주문 실행 |
| `config_validator.py` | [config_validator.md](./config_validator.md) | 설정 검증 |
| `portfolio_rebalancing.py` | [portfolio_rebalancing.md](./portfolio_rebalancing.md) | 메인 앱 |

### 설계서
- [Investment_portfolio.md](./Investment_portfolio.md) - 전체 시스템 설계서

### 개발 팁

#### 1. 로깅 활성화
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### 2. 특정 모듈만 테스트
```python
from modules.scheduler import PortfolioScheduler
from modules.config_loader import get_portfolio_config

config = get_portfolio_config()
scheduler = PortfolioScheduler(config)
print(scheduler.is_execution_time())
print(scheduler.get_next_execution_time())
```

#### 3. 포트폴리오 스냅샷 확인
```python
from modules.kis_portfolio_fetcher import KISPortfolioFetcher
from modules.kis_auth import KISAuth

auth = KISAuth(...)
fetcher = KISPortfolioFetcher(auth)
snapshot = fetcher.fetch_portfolio_snapshot("portfolio-001")

print(f"Cash: {snapshot.cash}")
print(f"Total: {snapshot.total_value}")
print(f"Weights: {snapshot.get_current_weights()}")
```

#### 4. 리밸런싱 계획 미리보기
```python
from modules.rebalancing_engine import RebalancingEngine

engine = RebalancingEngine(config)
plan = engine.create_rebalance_plan(snapshot)

print(f"Should rebalance: {plan.should_rebalance}")
print(f"Reason: {plan.rebalance_reason}")
for order in plan.orders:
    print(f"{order.ticker}: {order.action} {order.delta_value:.0f} KRW")
```

## Best Practices

### 개발 단계
1. ✅ `dry_run=true`로 시작
2. ✅ `--validate-only`로 설정 검증
3. ✅ `--mode once`로 한 번 실행 테스트
4. ✅ 스케줄 설정 테스트 (작은 interval에서)
5. ✅ 로그 파일 확인

### 배포 단계
1. ✅ 최종 설정 검증
2. ✅ 계좌번호 재확인
3. ✅ `dry_run=false`로 변경 (신중하게 결정)
4. ✅ 한 번만 실행해서 주문 확인
5. ✅ 스케줄러 모드로 전환

### 운영 단계
1. ✅ 정기적인 로그 확인
2. ✅ 월 1회 이상 포트폴리오 상태 검증
3. ✅ 분기마다 설정 리뷰
4. ✅ 로그 파일 로테이션

## FAQ

**Q: 목표 비중을 자주 변경해야 할 경우?**  
A: config_basic.json의 target_weights를 변경하고 애플리케이션을 재시작하면 됩니다.

**Q: 특정 시간에만 실행하려면?**  
A: `schedule/run_times` 배열에 원하는 시각을 추가하세요. (예: ["09:30", "14:00"])

**Q: 매매 수수료는 어떻게 반영되나?**  
A: 현재 버전에서는 반영되지 않습니다. `cost_model` 설정은 미구현 상태입니다.

**Q: 해외 주식도 지원되나?**  
A: 현재는 국내 주식(KOSPI, KOSDAQ)만 지원합니다. 해외 주식 확장은 미래 계획입니다.

## 라이선스 및 면책

이 프로젝트는 교육 및 개인 사용을 목적으로 제공됩니다.  
**⚠️ 실제 거래 사용 시 충분히 테스트한 후 본인의 책임하에 사용하세요.**

---

**마지막 업데이트:** 2026-02-16 (KIS API 에러 처리 개선)  
**작성자:** Investment Portfolio Rebalancing System  
**상태:** Production Ready (Dry-run mode) | Live testing (Live mode)
