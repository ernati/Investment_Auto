# KIS API 주식 거래 실패 문제 해결 가이드

## 문제 상황

2026년 2월 16일, Investment_Auto 포트폴리오 리밸런싱 애플리케이션에서 다음과 같은 오류가 발생했습니다:

```
Stock order (market buy): Unknown error (rt_cd=1)
Fetch holdings: Unknown error (rt_cd=2) 
Fetch account balance: Unknown error (rt_cd=2)
```

## 원인 분석

### 1. TR_ID 문제 (주요 원인)
- **문제**: kis_api_utils.py에서 구버전 TR_ID 사용
- **기존 코드**: `TTTC0802U`, `TTTC0801U`
- **정상 TR_ID**: `TTTC0012U`, `TTTC0011U`

### 2. API 파라미터 처리 문제
- **문제**: 계좌 번호 불필요한 슬라이싱 `account[:8]`
- **해결**: 계좌 번호 직접 사용 (이미 8자리)

### 3. 거래소 ID 설정 문제  
- **문제**: 모의투자에서 "SOR" 사용
- **해결**: 모의투자는 "KRX"만 지원

### 4. 에러 메시지 부족
- **문제**: RT_CD 코드만 표시, 상세 메시지 없음
- **해결**: MSG_CD, MSG1 필드 활용

## 해결 과정

### 1단계: TR_ID 수정 ✅

`kis_api_utils.py` 수정:
```python
# 수정 전
tr_id = "TTTC0802U" if normalized_action == "buy" else "TTTC0801U"

# 수정 후  
tr_id = "TTTC0012U" if normalized_action == "buy" else "TTTC0011U"
```

### 2단계: 계좌 번호 처리 개선 ✅

```python
# 수정 전
"CANO": kis_auth.account[:8]

# 수정 후
"CANO": kis_auth.account
```

### 3단계: 주문 실행 로직 개선 ✅

`order_executor.py`에서 `KISTrading` 모듈 직접 사용:
```python
# 수정 전: kis_api_utils.place_stock_order() 사용

# 수정 후: KISTrading 클래스 직접 사용
self.trading = KISTrading(kis_auth)
order_result = self.trading.buy_market_order(stock_code, quantity)
```

### 4단계: 거래소 ID 수정 ✅

`kis_trading.py`에서 기본값 변경:
```python
# 수정 전
excg_id_dvsn_cd: str = "SOR"

# 수정 후  
excg_id_dvsn_cd: str = "KRX"  # 모의투자는 KRX만 가능
```

### 5단계: 에러 처리 강화 ✅

`validate_api_response()` 개선:
```python
# MSG_CD, MSG1 필드 활용한 상세 에러 메시지 추출
if msg_cd and msg1:
    error_msg = f"[{msg_cd}] {msg1}"
```

### 6단계: 진단 도구 개발 ✅

`kis_diagnostic.py` 모듈 생성:
- 계좌 상태 진단
- 거래 가능 여부 확인  
- 주문 파라미터 검증
- 종합 진단 기능

## 수정된 파일 목록

| 파일 | 변경 내용 | 버전 |
|------|-----------|------|
| `kis_api_utils.py` | TR_ID 수정, 계좌번호 처리 개선, 에러 처리 강화 | v2.0 |
| `order_executor.py` | KISTrading 모듈 직접 사용 | v1.3 |
| `kis_trading.py` | 거래소 ID 기본값 변경, 디버깅 로그 추가 | v1.1 |
| `kis_diagnostic.py` | 🆕 새로 생성 - 진단 도구 | v1.0 |
| `kis_debug.py` | 🆕 새로 생성 - 명령줄 진단 스크립트 | v1.0 |

## 올바른 TR_ID 레퍼런스

| 거래 유형 | 실전투자 | 모의투자 | 비고 |
|-----------|----------|----------|------|
| 현금 매수 | TTTC0012U | VTTC0012U | ✅ 신버전 |
| 현금 매도 | TTTC0011U | VTTC0011U | ✅ 신버전 |
| ~~현금 매수~~ | ~~TTTC0802U~~ | ~~VTTC0802U~~ | ❌ 구버전 (사용금지) |
| ~~현금 매도~~ | ~~TTTC0801U~~ | ~~VTTC0801U~~ | ❌ 구버전 (사용금지) |

## 테스트 방법

### 1. 진단 도구 실행
```bash
cd Investment_Auto/Scripts/apps
python kis_debug.py
```

### 2. 수동 테스트
```python
from modules.kis_auth import KISAuth
from modules.kis_trading import KISTrading

# 인증 초기화 (모의투자)
auth = KISAuth(appkey, appsecret, account, env="demo")

# 거래 모듈 테스트
trading = KISTrading(auth)
result = trading.buy_limit_order("005930", 1, 1000)  # 낮은 가격으로 테스트

if result["success"]:
    print(f"✅ 주문 성공: {result['order_no']}")
else:
    print(f"❌ 주문 실패: {result['message']}")
```

## 예방 조치

### 1. 정기적인 API 문서 확인
- KIS 공식 문서: https://apiportal.koreainvestment.com/
- TR_ID 변경사항 모니터링

### 2. 진단 도구 정기 실행
- 월 1회 종합 진단 실행
- 새로운 환경 설정 시 필수 실행

### 3. 에러 로깅 강화
- RT_CD별 상세 에러 분류
- API 호출 파라미터 로깅

### 4. 테스트 환경 구축
- 모의투자 계좌를 통한 정기 테스트
- CI/CD 파이프라인에 API 테스트 포함

## 관련 문서

- [KIS API 유틸리티 문서](kis_api_utils.md)
- [KIS 진단 도구 문서](kis_diagnostic.md) 
- [주문 실행 모듈 문서](order_executor.md)
- [KIS 거래 모듈 문서](kis_trading.md)

## 추가 개선 사항

### 단기 개선 (1개월 내)
- [ ] 배치 주문 기능 추가
- [ ] 주문 취소/정정 기능 구현
- [ ] 실시간 체결 알림 기능

### 장기 개선 (3개월 내)  
- [ ] 비동기 API 호출 지원
- [ ] 다중 계좌 관리 기능
- [ ] 고급 주문 유형 지원 (IOC, FOK 등)

## 문의 및 지원

이 문제 해결 과정에서 발생한 질문이나 추가 개선사항은 GitHub Issues를 통해 문의해 주세요.