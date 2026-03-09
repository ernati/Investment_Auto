# KIS API 에러 분석 및 해결 방안

## 📅 분석 대상 로그
- **로그 날짜**: 2026-03-04 09:00:XX
- **애플리케이션**: Portfolio Rebalancing (모의투자)
- **주요 기능**: 포트폴리오 리밸런싱 및 주문 실행

## 🔍 발견된 에러 분석

### 1. 토큰 만료 에러 (EGW00123)

#### 에러 상세 정보
```
[EGW00123] 기간이 만료된 token 입니다. (HTTP 500)
```

#### 발생 위치
- **모듈**: `modules.kis_api_utils.py`
- **함수**: 주식 현재가 조회 (`Fetch stock price for 000660`)
- **발생 시간**: 2026-03-04 09:00:18~26

#### 원인 분석
- KIS API 액세스 토큰의 유효기간 만료 (24시간 유효)
- 토큰 갱신 로직이 호출되지 않거나 실패
- API 호출 시 만료된 토큰 사용으로 인한 연속 실패

#### 영향도
- **심각도**: 🔴 HIGH
- **영향 범위**: 전체 포트폴리오 조회 및 리밸런싱 기능 중단
- **비즈니스 영향**: 자동 투자 서비스 중단

---

### 2. 체결정보 조회 파라미터 에러 (OPSQ2001)

#### 에러 상세 정보
```
[OPSQ2001] ERROR : INPUT_FIELD_NAME CTX_AREA_FK100 (rt_cd=2)
```

#### 발생 위치
- **모듈**: `modules.kis_trading.py`
- **함수**: 체결정보 조회 (`_retry_execution_price`)
- **TR ID**: `VTTC8001R` (모의투자 주식일별주문체결조회)
- **발생 시간**: 2026-03-04 09:00:31~55

#### 원인 분석
- 페이지네이션 관련 파라미터 필드명 오류
- `FK100`, `NK100` → `CTX_AREA_FK100`, `CTX_AREA_NK100`으로 변경됨
- API 스펙 변경에 따른 호환성 문제

#### 영향도
- **심각도**: 🟡 MEDIUM
- **영향 범위**: 주문 체결가격 확인 실패
- **비즈니스 영향**: 정확한 포트폴리오 가치 산정 어려움

---

## 🛠️ 해결 방안

### 1. 토큰 자동 갱신 로직 개선

#### 수정된 파일
- [`Scripts/modules/kis_auth.py`](../Scripts/modules/kis_auth.py)
- [`Scripts/modules/kis_api_utils.py`](../Scripts/modules/kis_api_utils.py)

#### 주요 변경사항

1. **강제 토큰 갱신 기능 추가**
```python
def authenticate(self, force_refresh=False):
    # 강제 갱신 시 캐시된 토큰 무시하고 새로 발급
```

2. **토큰 만료 예측 및 사전 갱신**
```python
def is_token_expired(self):
    # 만료 5분 전부터 갱신하도록 Buffer 적용
    return (valid_date - now).total_seconds() < 300
```

3. **API 호출 시 자동 토큰 갱신**
```python
# EGW00123 에러 감지 시 자동 토큰 갱신 후 재시도
if "EGW00123" in error_msg and kis_auth is not None:
    kis_auth.authenticate(force_refresh=True)
    headers["authorization"] = f"Bearer {kis_auth.token}"
    continue  # 재시도
```

#### 기대 효과
- 토큰 만료로 인한 서비스 중단 방지
- 자동화된 토큰 관리로 운영 안정성 향상
- 사용자 개입 없는 연속적인 서비스 제공

---

### 2. 체결정보 조회 API 파라미터 수정

#### 수정된 파일
- [`Scripts/modules/kis_trading.py`](../Scripts/modules/kis_trading.py)

#### 주요 변경사항

1. **올바른 파라미터 필드명 사용**
```python
params = {
    "CTX_AREA_FK100": "",  # 기존: "FK100"
    "CTX_AREA_NK100": "",  # 기존: "NK100"
    # ... 기타 파라미터
}
```

2. **조회 로직 개선**
```python
# 전체 조회 후 주문번호와 종목코드로 매칭
if order_odno == order_no and order_pdno == stock_code:
    # 체결정보 추출
```

3. **에러 처리 강화**
```python
# OPSQ2001 에러는 재시도해도 해결되지 않으므로 중단
if "OPSQ2001" in error_msg:
    break
```

#### 기대 효과
- 체결정보 조회 성공률 향상
- 정확한 포트폴리오 가치 산정
- 불필요한 재시도 방지로 성능 개선

---

## 📊 추가 개선 권장사항

### 1. 모니터링 강화
- 토큰 만료 임박 시 알림 시스템 구축
- API 에러율 모니터링 대시보드 구축
- 체결정보 조회 성공률 추적

### 2. 에러 복구 전략
- Circuit Breaker 패턴 도입
- Fallback 메커니즘 구현 (대체 가격 소스 등)
- 장애 상황별 복구 시나리오 정의

### 3. 테스트 커버리지 확대
- 토큰 만료 시나리오 테스트
- API 파라미터 검증 자동화
- 통합 테스트 환경 구축

---

## 🔗 관련 리소스

### API 문서
- [한국투자증권 Open API 문서](https://apiportal.koreainvestment.com/)
- [에러코드 가이드](https://apiportal.koreainvestment.com/faq-error-code)

### 디버깅 도구
- [`Scripts/tests/kis_debug.py`](../Scripts/tests/kis_debug.py) - KIS API 디버깅 스크립트

### 설정 파일
- [`Config/config.json`](../Config/config.json) - KIS API 인증 정보
- [`Config/database.json`](../Config/database.json) - 데이터베이스 설정

---

## 📝 작업 이력

| 날짜 | 작업자 | 내용 | 상태 |
|------|--------|------|------|
| 2026-03-04 | GitHub Copilot | 토큰 자동 갱신 로직 개선 | ✅ 완료 |
| 2026-03-04 | GitHub Copilot | 체결정보 조회 API 파라미터 수정 | ✅ 완료 |
| 2026-03-04 | GitHub Copilot | 에러 분석 문서 작성 | ✅ 완료 |

---

*이 문서는 `Scripts/modules/kis_trading.py` 관련 에러 분석 및 해결 방안을 담고 있습니다.*