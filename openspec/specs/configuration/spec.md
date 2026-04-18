# Spec: Configuration

**Capability:** `configuration`  
**Source:** `Scripts/modules/config_loader.py`, `Config/`  
**Last synced:** 2026-04-18

---

## Purpose

시스템의 모든 설정을 파일에서 로드하고, 모듈에 주입한다. 두 개의 독립적인 설정 체계가 존재한다: KIS/Upbit API 인증 정보(`config.json`)와 포트폴리오 리밸런싱 설정(`config_basic.json` + `config_advanced.json`).

---

## 파일 구조

```
Config/
  config.json           ← KIS/Upbit API 키 (ConfigLoader)
  config_basic.json     ← 포트폴리오 기본 설정 (PortfolioConfigLoader)
  config_advanced.json  ← 고급/위험 설정 (PortfolioConfigLoader, 선택)
```

**config_basic.json**: 필수. 없으면 `FileNotFoundError` → 앱 시작 불가.  
**config_advanced.json**: 선택. 없어도 경고 로그만 출력, 빈 dict로 처리.  
**config.json**: 필수 (KIS 인증). 없으면 `FileNotFoundError`.

---

## 로더 클래스

### ConfigLoader (config.json 전용)

```python
loader = get_config()           # 전역 싱글톤

loader.get("kis.real.appkey")   # 점(.) 구분자
loader.get_kis_config("real")   # → {"appkey": ..., "appsecret": ..., "account": ..., ...}
loader.get_kis_config("demo")
loader.get_upbit_config("real")
loader.get_upbit_config("demo")
```

### PortfolioConfigLoader (basic + advanced)

```python
loader = get_portfolio_config()  # 전역 싱글톤

loader.get("rebalance/mode")         # merged (advanced 우선)
loader.get_basic("rebalance/mode")   # basic 전용
loader.get_advanced("risk_guardrails/max_single_order_krw")  # advanced 전용
```

**키 구분자:** PortfolioConfigLoader는 슬래시(`/`), ConfigLoader는 점(`.`)

---

## Merge 동작

```
config_basic.json + config_advanced.json → deep merge

규칙:
  - 두 파일 모두 dict인 경우: 재귀적 merge
  - 그 외: advanced 값이 basic을 override

예시:
  basic:    {"trade": {"cash_buffer_ratio": 0.02, "min_order_krw": 100000}}
  advanced: {"trade": {"min_order_krw": 500000}}
  merged:   {"trade": {"cash_buffer_ratio": 0.02, "min_order_krw": 500000}}
```

`get()` = merged 결과에서 읽음.  
`get_basic()` = merged 이전 basic에서만 읽음.  
`get_advanced()` = advanced에서만 읽음 (없으면 default).

---

## config.json 스키마

```json
{
  "kis": {
    "real": {
      "appkey": "...",
      "appsecret": "...",
      "account": "XXXXXXXX",
      "product": "01",
      "htsid": "..."
    },
    "demo": {
      "appkey": "...",
      "appsecret": "...",
      "account": "XXXXXXXX",
      "product": "01",
      "htsid": "..."
    }
  },
  "upbit": {
    "real": {
      "access_key": "...",
      "secret_key": "..."
    },
    "demo": {
      "access_key": "...",
      "secret_key": "..."
    }
  }
}
```

---

## config_basic.json 스키마

```json
{
  "portfolio_id": "my-portfolio",
  "base_currency": "KRW",

  "target_weights": {
    "stocks": {
      "005930": 0.30,
      "069500": 0.20
    },
    "bonds": {
      "114820": 0.10
    },
    "overseas_stocks": {
      "AAPL": { "exchange": "NASD", "weight": 0.15 },
      "SPY":  { "exchange": "NYSE", "weight": 0.10 }
    },
    "coin": {
      "bitcoin": 0.15
    }
  },

  "rebalance": {
    "mode": "HYBRID",              // "BAND" | "CALENDAR" | "HYBRID"
    "price_source": "last",        // "last" | "close"
    "band": {
      "type": "ABS",               // "ABS" | "REL"
      "value": 0.05
    },
    "schedule": {
      "timezone": "Asia/Seoul",
      "run_times": ["09:00", "15:20"],
      "calendar_rules": {
        "hourly": {
          "enabled": false,
          "minute": 0
        },
        "month_end": false,
        "quarter_end": false,
        "weekly": {
          "enabled": false,
          "weekday": "FRI"          // MON|TUE|WED|THU|FRI|SAT|SUN
        }
      },
      "market_hours": {
        "enabled": true
      }
    }
  },

  "trade": {
    "cash_buffer_ratio": 0.02,
    "min_order_krw": 100000
  }
}
```

---

## config_advanced.json 스키마

```json
{
  "order_policy": {
    "order_type": "market"          // "market" | "limit"
  },

  "risk_guardrails": {
    "max_single_order_krw": null,   // null = 비활성화
    "max_orders_per_run": null,
    "max_turnover_per_run": null    // 0.0~1.0 비율
  },

  "run_limit": {
    "max_runs_per_day": 999
  }
}
```

`null` 값 → 해당 가드레일 비활성화.  
파일 전체가 없어도 동일하게 모두 비활성화.

---

## 전역 싱글톤

```python
# 최초 호출 시 load() 자동 실행
config = get_config()              # ConfigLoader 싱글톤
portfolio_config = get_portfolio_config()  # PortfolioConfigLoader 싱글톤

# 강제 리로드
config = get_config(reload=True)
portfolio_config = get_portfolio_config(reload=True)
```

**주의:** 싱글톤은 프로세스 생애 동안 유지됨. 설정 파일 변경은 프로세스 재시작 필요.  
`PortfolioWebServer.__init__`에서 `get_portfolio_config()`를 직접 호출하므로 기존 싱글톤과 동일 인스턴스 공유.

---

## ConfigValidator 연동

`ConfigValidator`는 `PortfolioConfigLoader`를 받아 시작 시 1회 실행.  
검증 실패 시 `RuntimeError` → 앱 시작 불가.

주요 검증 항목 (별도 모듈, `config_validator.py`):
- `portfolio_id` 존재 여부
- `target_weights` 합계 = 1.0 여부
- 필수 KIS API 키 존재 여부

---

## Invariants

1. `config_basic.json` 없으면 `FileNotFoundError` → 앱 시작 불가
2. `config.json` 없으면 `FileNotFoundError` → 앱 시작 불가
3. `config_advanced.json` 없으면 모든 고급 기능 기본값 사용 (오류 없음)
4. 설정은 런타임 변경 불가 — 파일 수정 후 재시작 필요
5. `overseas_stocks`의 weight 합산은 다른 카테고리와 동일하게 `target_weights` 합계에 포함

---

## 파일 경로 기준

```
ConfigLoader    → {project_root}/Config/config.json
PortfolioConfigLoader → {project_root}/Config/config_basic.json
                        {project_root}/Config/config_advanced.json

project_root = Path(__file__).parent.parent.parent  (from Scripts/modules/)
             = Investment_Auto/
```
