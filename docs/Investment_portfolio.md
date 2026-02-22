# 포트폴리오 자동 리밸런싱 시스템 설계서 (설정 참조 기반)

본 문서는 “목표 비중 유지(리밸런싱)”를 자동화하는 시스템을 정의한다.
문서 내에서는 숫자/상수 값을 직접 하드코딩하지 않고, 설정 파일의 경로를 통해 값을 참조한다.

---

## 0. 설정 파일 규격

### 0.1 설정 파일 구성
- ../Config/config_basic.json : 일반 고객이 조정하는 기본 설정
- ../Config/config_advanced.json : 운영/전문가가 조정하는 세부 설정

### 0.2 설정 로드 및 우선순위
1) 시스템은 ../Config/config_basic.json을 먼저 로드한다. (필수)
2) 시스템은 ../Config/config_advanced.json을 다음으로 로드한다. (선택이지만 LIVE에서는 사실상 필수)
3) 두 파일에 동일한 키가 존재하면 ../Config/config_advanced.json 값이 우선한다. (deep merge)

### 0.3 설정 참조 표기 규칙
- BASIC 설정 참조: BASIC:/path/to/value
- ADV 설정 참조: ADV:/path/to/value

---

## 1. 목적 및 핵심 개념
- 종목평가 = 보유수량 * 가격
- 총평가 = Σ(종목평가) + 현금
- 현재비중_i = 종목평가_i / 총평가
- 목표비중_i = 설정된 목표 비중
- 드리프트_i = 현재비중_i - 목표비중_i

---

## 2. 설정 항목 정의

### 2.1 Basic (config_basic.json)
- BASIC:/portfolio_id [REQUIRED]
- BASIC:/base_currency [REQUIRED]
- BASIC:/target_weights [REQUIRED] (합 1.0)
- BASIC:/rebalance/* [REQUIRED]
  - BASIC:/rebalance/mode [REQUIRED] ("BAND" | "CALENDAR" | "HYBRID")
  - BASIC:/rebalance/price_source [REQUIRED] ("close" | "last")
  - BASIC:/rebalance/schedule/* [REQUIRED]
- BASIC:/trade/* [REQUIRED]
  - BASIC:/trade/cash_buffer_ratio [REQUIRED]
  - BASIC:/trade/min_order_krw [REQUIRED]
- BASIC:/dry_run [REQUIRED]

### 2.2 Advanced (config_advanced.json)
- ADV:/run_limit/max_runs_per_day [OPTIONAL]
- ADV:/order_policy/* [OPTIONAL]
- ADV:/risk_guardrails/* [OPTIONAL but STRONGLY RECOMMENDED]
- ADV:/cost_model/* [OPTIONAL]
- ADV:/logging/*, ADV:/alerts/* [OPTIONAL]
- ADV:/integrations/* [REQUIRED for LIVE]

---

## 3. 스케줄(언제 측정하고 언제 실행하는가)

### 3.1 스케줄 입력
- 타임존: BASIC:/rebalance/schedule/timezone [REQUIRED]
- 실행 시각 목록: BASIC:/rebalance/schedule/run_times [OPTIONAL]
- 달력 규칙: BASIC:/rebalance/schedule/calendar_rules [OPTIONAL]
  - 월말/분기말/주간 등의 “정기 조건”
  - 테스트용: 매 정각 실행(hourly)

### 3.2 스케줄 우선순위(명확히 고정)
- 만약 BASIC:/rebalance/schedule/calendar_rules/hourly/enabled == true 이면:
  - 스케줄러는 **hourly 규칙만 사용**한다.
  - 이 경우 BASIC:/rebalance/schedule/run_times 값은 **무시**한다.
- hourly가 비활성(enabled=false)이면:
  - 스케줄러는 run_times에 지정된 시각에 실행 이벤트를 만든다.

### 3.3 hourly 규칙(테스트용)
- BASIC:/rebalance/schedule/calendar_rules/hourly/enabled == true 인 경우,
  - BASIC:/rebalance/schedule/calendar_rules/hourly/minute 분에
  - **매 시간마다** 실행 이벤트를 생성한다.
  - 예: minute=0 → 10:00, 11:00, 12:00, ...

### 3.4 실행 제한
- 하루 실행 횟수 제한: ADV:/run_limit/max_runs_per_day
- hourly 테스트를 수행하려면 max_runs_per_day가 24 이상이어야 한다(또는 충분히 큰 값).

---

## 4. 리밸런싱 모드(실행 이벤트 시 무엇을 하는가)

실행 이벤트가 발생하면 아래 순서로 처리한다.

1) 데이터 수집(스냅샷 생성)
- 현금, 보유수량: Broker Adapter
- 가격: Market Data Adapter (BASIC:/rebalance/price_source 기준)
- total_value 계산

2) 실행 필요 여부 판단
- mode = BASIC:/rebalance/mode
  - BAND: 밴드 이탈 시에만 주문 생성
  - CALENDAR: 정기 조건이 참일 때만 주문 생성
  - HYBRID: BAND 또는 CALENDAR 조건 중 하나라도 참이면 주문 생성

3) 주문 계획 생성(목표 비중 기반)
- cash_buffer_ratio = BASIC:/trade/cash_buffer_ratio
- usable_total = total_value * (1 - cash_buffer_ratio)
- target_weights = BASIC:/target_weights
- delta_i = (usable_total * target_weight_i) - current_value_i

4) 주문 스킵 규칙
- min_order_krw = BASIC:/trade/min_order_krw
- 주문금액이 min_order_krw 미만이면 스킵

5) 실행(매도→매수)
- 기본 순서: 매도 후 매수(현금 확보)
- 주문 타입/재시도 등은 ADV:/order_policy/* 를 따른다(없으면 안전 기본 정책)

6) 가드레일 검사
- ADV:/risk_guardrails/* 값이 존재하면 적용한다.
- 없으면 안전 기본값으로 동작한다.

---

## 5. LIVE 연동 요구사항
- BASIC:/dry_run == false 인 경우:
  - ADV:/integrations/broker/* 는 필수다.
  - ADV:/integrations/market_data/* 는 가격 제공 방식에 따라 필수/선택이다.

---

## 6. 설정 검증 규칙(구현 필수)
1) BASIC:/target_weights 합계는 1.0
2) BASIC:/rebalance/mode 가 BAND 또는 HYBRID이면 BASIC:/rebalance/band/* 필수
3) BASIC:/trade/cash_buffer_ratio 는 0~1
4) BASIC:/trade/min_order_krw 는 0 이상의 정수
5) LIVE 모드(dry_run=false)에서는 ADV:/integrations/broker/* 필수
