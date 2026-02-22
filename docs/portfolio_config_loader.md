# Portfolio Config Loader Module (config_loader.py - Updated)

## 개요
포트폴리오 리밸런싱 시스템을 위한 설정 파일 로더입니다.
`config_basic.json`과 `config_advanced.json` 두 파일을 로드하고 deep merge하여 통합된 설정을 제공합니다.

## 주요 기능

### 1. 이중 설정 파일 지원
- **config_basic.json** (필수): 일반 사용자가 조정하는 기본 설정
  - 포트폴리오 ID, 목표 비중, 리밸런싱 모드, 스케줄 등
  
- **config_advanced.json** (선택): 운영/전문가가 조정하는 세부 설정  
  - 실행 횟수 제한, 주문 정책, 위험 가드레일, 로깅 설정 등

### 2. Deep Merge 방식
```
기본 설정만 있는 경우:
config: basic만 사용

advanced도 있는 경우:
config: basic + advanced (동일 키는 advanced가 우선)
```

- 중첩된 딕셔너리를 재귀적으로 merge
- 설정 값 추가는 환영하지만, 제거는 불가능
- 설정 로드 후 동적 변경 불가 (불변)

### 3. 설정 참조 기능
설계서X의 "설정 참조 표기 규칙" 지원:

```
BASIC:/portfolio_id          → config.get_basic("portfolio_id")
BASIC:/rebalance/mode        → config.get_basic("rebalance/mode")
ADV:/run_limit/max_runs...   → config.get_advanced("run_limit/max_runs_per_day")
```

### 4. 기본값 지원
설정 없이 호출하면 기본값 반환:

```python
default_value = config.get("missing_key", default="default_value")
→ "default_value" 반환
```

## 사용 예시

### 기본 사용법
```python
from modules.config_loader import get_portfolio_config

# 싱글톤 패턴으로 전역 인스턴스 가져오기
config = get_portfolio_config()

# 설정 로드 (자동으로 basic + advanced merge)
merged_config = config.load()
```

### 설정 값 접근

#### Merged 설정에서 조회 (권장)
```python
# 두 파일 모두 확인, advanced가 있으면 우선
portfolio_id = config.get("portfolio_id")
mode = config.get("rebalance/mode")
dry_run = config.get("dry_run")

# 기본값 지정
timezone = config.get("rebalance/schedule/timezone", default="Asia/Seoul")
```

#### 기본 설정만 조회
```python
# config_basic.json에서만 가져오기
target_weights = config.get_basic("target_weights")
cash_buffer = config.get_basic("trade/cash_buffer_ratio")
schedule = config.get_basic("rebalance/schedule")
```

#### 고급 설정만 조회
```python
# config_advanced.json에서만 가져오기
max_runs = config.get_advanced("run_limit/max_runs_per_day")
max_turnover = config.get_advanced("risk_guardrails/max_turnover_per_run")
broker_id = config.get_advanced("integrations/broker/account_id")

# 없으면 기본값 반환
order_type = config.get_advanced("order_policy/order_type", default="market")
```

#### 전체 설정 반환
```python
# Merged 설정 딕셔너리 전체 반환
full_config = config.get_merged()

import json
print(json.dumps(full_config, indent=2))
```

## 설정 파일 구조

### config_basic.json (예시)
```json
{
  "portfolio_id": "portfolio-001",
  "base_currency": "KRW",
  "target_weights": {
    "005930": 0.50,
    "000660": 0.30,
    "035420": 0.20
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
      "run_times": ["09:30", "14:00"],
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
  "dry_run": true
}
```

### config_advanced.json (예시)
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

## 클래스 설명

### PortfolioConfigLoader
포트폴리오 리밸런싱용 설정 로더 클래스

#### 생성자
```python
PortfolioConfigLoader(config_dir: Optional[Path] = None)
```

- `config_dir`: 설정 파일 디렉토리
  - 기본값: `{프로젝트_루트}/Config/`
  - 설정 파일: `config_basic.json`, `config_advanced.json`

#### 속성
| 속성 | 설명 |
|------|------|
| `basic_config` | 기본 설정 딕셔너리 |
| `advanced_config` | 고급 설정 딕셔너리 |
| `merged_config` | Merge된 설정 딕셔너리 |

#### 메서드

| 메서드 | 설명 |
|--------|------|
| `load()` | 설정 파일 로드 및 merge |
| `get(key_path, default)` | Merged 설정에서 조회 |
| `get_basic(key_path, default)` | 기본 설정에서만 조회 |
| `get_advanced(key_path, default)` | 고급 설정에서만 조회 |
| `get_merged()` | 전체 merged 설정 반환 |

## 경로 표기법

키패스는 슬래시(`/`)로 구분합니다:
- `"portfolio_id"` → 최상위 레벨
- `"rebalance/mode"` → 중첩 레벨
- `"risk_guardrails/max_turnover_per_run"` → 깊은 중첩

## 에러 처리

```python
from modules.config_loader import PortfolioConfigLoader

try:
    config = PortfolioConfigLoader()
    config.load()
except FileNotFoundError as e:
    print(f"설정 파일 없음: {e}")
except json.JSONDecodeError as e:
    print(f"JSON 파싱 오류: {e}")
```

## 글로벌 인스턴스

```python
from modules.config_loader import get_portfolio_config

# 싱글톤 패턴: 한 번만 로드되고 이후 재사용
config = get_portfolio_config()

# reload=True로 다시 로드
config = get_portfolio_config(reload=True)
```

## 설정 검증

설정 로드 후 반드시 검증 모듈을 사용하여 검증하세요:

```python
from modules.config_validator import ConfigValidator

config = get_portfolio_config()
validator = ConfigValidator(config)
success, errors, warnings = validator.validate()

if not success:
    for error in errors:
        print(f"❌ {error}")
```

## 주의사항

1. **로드 순서**: basic이 먼저, advanced가 나중에 로드됨
2. **우선순위**: 동일 키는 advanced가 항상 우선
3. **필수 파일**: config_basic.json은 필수, config_advanced.json은 선택
4. **경로 표기**: 슬래시(`/`)로 구분, 점(`.`)이 아님
5. **불변성**: 로드 후 동적 변경 불가 (다시 로드해야 함)

## 성능 주의사항

- 설정 파일은 애플리케이션 시작 시 한 번만 로드
- Deep merge는 설정 크기가 작아서 성능 영향 무시할 수 있음
- 글로벌 인스턴스는 싱글톤으로 관리되어 메모리 효율적
