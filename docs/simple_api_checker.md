# Simple API Checker 문서

## 개요

`simple_api_checker.py`는 KIS Open Trading API의 기본적인 연결 상태와 핵심 기능들을 빠르게 점검하는 간단한 진단 도구입니다. 복잡한 의존성 없이 독립적으로 실행 가능하도록 설계되었습니다.

## 주요 특징

### 1. 독립 실행 가능
- 기존 모듈의 import 문제를 회피
- 최소한의 외부 의존성 (requests 라이브러리만 필요)
- 설정 파일만 있으면 즉시 실행 가능

### 2. 핵심 API 테스트
- **인증 테스트**: Access Token 발급 여부
- **계좌 잔고 조회**: 현금 및 자산 정보 접근성
- **주식 보유 현황**: 포트폴리오 데이터 조회
- **주식 가격 조회**: 실시간 시세 접근성

### 3. 명확한 결과 표시
- 성공/실패 상태를 명확하게 표시
- 오류 원인 및 상세 정보 제공
- 전체 성공률 및 요약 정보

## 사용법

### 기본 실행
```bash
# 모의투자 환경 테스트
python simple_api_checker.py demo

# 실전투자 환경 테스트
python simple_api_checker.py real
```

### 실행 전 준비사항
1. **설정 파일 확인**: `../../Config/config.json`이 올바르게 설정되어 있는지 확인
2. **네트워크 연결**: 인터넷 연결 상태 확인
3. **Python 환경**: requests 라이브러리 설치 (`pip install requests`)

## 출력 해석

### 성공 사례
```
✅ PASS Authentication: Successfully obtained access token
✅ PASS Stock Price: Successfully retrieved price for 005930
```

### 실패 사례
```
❌ FAIL Account Balance: Failed: API error: Unknown error (rt_cd=2)
```

### 요약 정보
```
📊 KIS API Health Check Summary (DEMO Environment)
============================================================
Total Tests: 4
✅ Passed: 3
❌ Failed: 1
Success Rate: 75.0%
```

## 테스트 항목 상세

### 1. Authentication (인증)
**목적**: API 접근 권한 확인
```python
# 테스트 내용
- Access Token 발급 요청
- 토큰 유효성 검증
- 토큰 길이 확인
```

**성공 조건**: 유효한 Access Token 반환
**실패 원인**: 잘못된 API Key/Secret, 네트워크 오류

### 2. Account Balance (계좌 잔고)
**목적**: 계좌 정보 접근 권한 확인
```python
# API 엔드포인트
/uapi/domestic-stock/v1/trading/inquire-balance

# TR ID
CTRP6504R (모의투자에서는 VTRP6504R)
```

**성공 조건**: rt_cd='0' 및 계좌 정보 반환
**실패 원인**: 권한 부족, 파라미터 오류, 서버 문제

### 3. Stock Holdings (주식 보유 현황)
**목적**: 포트폴리오 데이터 접근성 확인
```python
# API 엔드포인트
/uapi/domestic-stock/v1/trading/inquire-balance

# TR ID
TTTC8434R (모의투자에서는 VTTC8434R)
```

**성공 조건**: 보유 종목 리스트 반환 (빈 리스트도 성공)
**실패 원인**: API 파라미터 오류, 서버 응답 지연

### 4. Stock Price (주식 가격)
**목적**: 실시간 시세 데이터 접근성 확인
```python
# API 엔드포인트
/uapi/domestic-stock/v1/quotations/inquire-price

# 기본 테스트 종목
005930 (삼성전자)
```

**성공 조건**: 유효한 주식 가격 반환
**실패 원인**: 잘못된 종목코드, 시세 서버 오류

## 클래스 구조

### SimpleKISAPIChecker
```python
class SimpleKISAPIChecker:
    def __init__(self, env: str = "demo")
    def _load_config(self)              # 설정 파일 로드
    def _authenticate(self) -> bool     # API 인증
    def _build_headers(self, tr_id: str) -> Dict[str, str]  # 헤더 생성
    def _api_request(self, ...)         # API 요청 실행
    def test_account_balance(self) -> bool    # 계좌 잔고 테스트
    def test_stock_price(self, ticker: str) -> bool  # 주식 가격 테스트
    def test_stock_holdings(self) -> bool     # 보유 현황 테스트
    def run_tests(self) -> bool         # 전체 테스트 실행
    def print_summary(self)             # 결과 요약 출력
```

## 오류 코드 해석

### KIS API rt_cd 값
- **'0'**: 성공
- **'2'**: 일반적인 오류 (파라미터 문제, 권한 부족 등)
- **기타**: 특정 오류 상황

### HTTP 상태 코드
- **200**: 정상 응답
- **401**: 인증 실패
- **500**: 서버 내부 오류
- **기타**: 네트워크 또는 서버 문제

## 문제 해결 가이드

### 1. Authentication 실패
```python
❌ FAIL Authentication: Authentication failed: 401 Client Error
```
**해결책**: 
- config.json의 appkey, appsecret 재확인
- API 서비스 활성화 상태 확인

### 2. Account Balance rt_cd=2
```python
❌ FAIL Account Balance: Failed: API error: Unknown error (rt_cd=2)
```
**해결책**:
- 계좌번호 형식 확인 (8자리)
- 상품코드 정확성 검증
- KIS 고객센터 문의

### 3. Connection Timeout
```python
❌ FAIL: Failed: HTTPSConnectionPool timeout
```
**해결책**:
- 네트워크 연결 상태 확인
- 방화벽 설정 점검
- 재시도 후 지속 시 KIS 서버 상태 확인

## 확장 방법

### 1. 추가 API 테스트
```python
def test_order_inquiry(self) -> bool:
    """주문 내역 조회 테스트"""
    # 구현 내용...
```

### 2. 다른 종목 가격 테스트
```python
# 여러 종목 동시 테스트
tickers = ['005930', '000660', '035420']
for ticker in tickers:
    success = checker.test_stock_price(ticker)
```

### 3. 결과 저장 기능
```python
def save_results(self, filename: str):
    """테스트 결과를 파일로 저장"""
    with open(filename, 'w') as f:
        json.dump(self.results, f, indent=2)
```

## 관련 파일

- **설정 파일**: `Config/config.json`
- **원본 API 체커**: `api_health_checker.py` (더 복잡하지만 기능 풍부)
- **실제 사용 모듈**: `modules/kis_auth.py`, `modules/kis_api_utils.py`

## 사용 시나리오

### 일일 점검
```bash
# 매일 아침 API 상태 확인
python simple_api_checker.py demo > daily_check.log
```

### 긴급 진단
```bash
# 시스템 오류 발생 시 즉시 진단
python simple_api_checker.py demo
```

### 환경 전환 전 확인
```bash
# 실전 환경 전환 전 상태 점검
python simple_api_checker.py real
```

## 주의사항

1. **Rate Limiting**: 과도한 테스트는 API 호출 제한에 걸릴 수 있습니다
2. **실전 환경**: real 환경 테스트는 신중하게 진행하세요
3. **민감 정보**: 로그에 access token이 포함되지 않도록 주의하세요
4. **네트워크**: 환경에 따라 timeout 값 조정이 필요할 수 있습니다

## 기술적 특징

### 설계 철학
- **단순함**: 복잡한 의존성 없이 핵심 기능만 테스트
- **신뢰성**: 안정적인 독립 실행
- **명확성**: 성공/실패를 즉시 판단 가능

### 성능 특징
- **빠른 실행**: 전체 테스트 약 3-5초 소요
- **낮은 리소스**: 메모리 사용량 최소화
- **즉시 피드백**: 실시간으로 테스트 결과 표시

---

**작성일**: 2026-02-11  
**버전**: 1.0  
**호환성**: Python 3.8+, KIS Open Trading API v1