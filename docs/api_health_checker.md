# KIS API Health Checker 문서

## 개요

`api_health_checker.py`는 한국투자증권(KIS) Open Trading API의 상태를 점검하는 진단 도구입니다. API 연결 문제를 신속하게 식별하고 해결하는 데 도움을 줍니다.

## 주요 기능

### 1. API 인증 테스트
- Access Token 발급 가능 여부 확인
- 인증 정보 유효성 검증
- 토큰 길이 및 형식 확인

### 2. 계좌 관련 API 테스트
- **계좌 잔고 조회**: 현금 잔고 및 총 자산 조회 가능 여부
- **주식 보유 현황**: 보유 종목 리스트 조회 가능 여부
- **주문 내역 조회**: 당일 주문 내역 조회 가능 여부

### 3. 시세 관련 API 테스트
- **주식 가격 조회**: 특정 종목의 현재가 조회 가능 여부
- **시장 상태 조회**: 장 운영 시간 및 휴장일 확인

### 4. 추가 API 테스트 (Full Test 모드)
- **시장 운영 정보**: 휴장일 조회 등 확장 기능 테스트

## 사용법

### 기본 사용법
```bash
# 모의투자 환경에서 기본 테스트 실행
python api_health_checker.py --env demo

# 실전투자 환경에서 전체 테스트 실행
python api_health_checker.py --env real --full-test
```

### 고급 사용법
```bash
# 특정 종목으로 가격 조회 테스트
python api_health_checker.py --env demo --ticker 000660

# 테스트 결과를 JSON 파일로 저장
python api_health_checker.py --env demo --output health_check_results.json

# 전체 옵션을 사용한 완전한 테스트
python api_health_checker.py --env demo --full-test --ticker 005930 --output detailed_results.json
```

## 명령행 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--env` | API 환경 (demo/real) | demo |
| `--full-test` | 전체 테스트 실행 | False |
| `--output` | 결과 파일 경로 (JSON) | 자동 생성 |
| `--ticker` | 가격 조회 대상 종목코드 | 005930 |

## 테스트 항목 상세

### 1. Authentication (인증)
- **목적**: API 인증이 정상적으로 이루어지는지 확인
- **확인 사항**: Access Token 발급 성공 여부
- **실패 원인**: 잘못된 API Key/Secret, 네트워크 문제

### 2. Account Balance Query (계좌 잔고 조회)
- **목적**: 계좌 정보 조회 권한 및 API 정상 작동 확인
- **확인 사항**: 계좌 잔고 및 자산 정보 조회 성공
- **실패 원인**: 계좌 권한 부족, API 서버 오류

### 3. Stock Holdings Query (보유 주식 조회)
- **목적**: 포트폴리오 정보 조회 기능 확인
- **확인 사항**: 보유 종목 리스트 조회 성공
- **실패 원인**: API 파라미터 오류, 서버 응답 지연

### 4. Stock Price Query (주식 가격 조회)
- **목적**: 시세 정보 조회 기능 확인
- **확인 사항**: 특정 종목의 현재가 조회 성공
- **실패 원인**: 잘못된 종목코드, 시세 서버 오류

### 5. Order Inquiry (주문 조회)
- **목적**: 주문 관리 기능 확인
- **확인 사항**: 주문 내역 조회 성공
- **실패 원인**: 주문 권한 부족, API 서버 점검

## 출력 형식

### 콘솔 출력
```
🔍 Starting basic API health checks...
✅ PASS Authentication: Successfully obtained access token
❌ FAIL Account Balance Query: Account balance query failed: 500 Server Error
...

📊 KIS API Health Check Summary (DEMO Environment)
============================================================
Total Tests: 5
✅ Passed: 3
❌ Failed: 2
Success Rate: 60.0%

❌ Failed Tests:
  • Account Balance Query: Account balance query failed: 500 Server Error
  • Stock Price Query: Stock price query failed for 005930: 500 Server Error
```

### JSON 출력 파일
```json
{
  "environment": "demo",
  "timestamp": "2026-02-11T15:30:45",
  "summary": {
    "total_tests": 5,
    "passed_tests": 3,
    "failed_tests": 2,
    "success_rate": 0.6
  },
  "test_results": [
    {
      "test_name": "Authentication",
      "success": true,
      "message": "Successfully obtained access token",
      "timestamp": "2026-02-11T15:30:45",
      "details": {
        "token_length": 1024
      }
    }
  ]
}
```

## 문제 해결 가이드

### 일반적인 오류와 해결책

#### 1. Authentication 실패
**증상**: "Failed to obtain access token"
**원인**: 
- 잘못된 API Key 또는 Secret
- 계정 비활성화
- 네트워크 연결 문제

**해결책**:
1. `config.json`의 API Key/Secret 재확인
2. KIS 홈페이지에서 API 서비스 활성화 상태 확인
3. 네트워크 연결 및 방화벽 설정 확인

#### 2. HTTP 500 Server Error
**증상**: "500 Server Error: Internal Server Error"
**원인**:
- KIS API 서버 점검 또는 장애
- 요청 파라미터 오류
- 계정별 API 호출 한도 초과

**해결책**:
1. KIS 공지사항에서 서버 점검 일정 확인
2. API 호출 빈도 줄이기 (Rate Limiting)
3. 파라미터 값 재검토

#### 3. Connection Timeout
**증상**: "Request timeout after 10s"
**원인**:
- 네트워크 연결 불안정
- API 서버 응답 지연
- 방화벽에 의한 차단

**해결책**:
1. 네트워크 연결 상태 확인
2. `timeout` 값 증가 고려
3. 프록시 또는 VPN 설정 확인

## 관련 파일

- **설정 파일**: `Config/config.json`
- **인증 모듈**: `Scripts/modules/kis_auth.py`
- **API 유틸리티**: `Scripts/modules/kis_api_utils.py`
- **설정 로더**: `Scripts/modules/config_loader.py`

## 사용 예시 시나리오

### 시나리오 1: 일일 점검
```bash
# 매일 아침 API 상태 점검
python api_health_checker.py --env demo --output daily_check.json
```

### 시나리오 2: 문제 발생 시 진단
```bash
# API 오류 발생 시 상세 진단
python api_health_checker.py --env demo --full-test --ticker 005930
```

### 시나리오 3: 실전 환경 점검
```bash
# 실전 투자 전 최종 점검
python api_health_checker.py --env real --full-test --output production_check.json
```

## 주의사항

1. **Rate Limiting**: KIS API는 초당 호출 횟수에 제한이 있습니다. 과도한 테스트는 피해주세요.
2. **실전 환경**: `--env real` 옵션 사용 시 실제 계좌에 영향을 줄 수 있으므로 주의하세요.
3. **API Key 보안**: 결과 파일에는 민감한 정보가 포함되지 않지만, 로그 파일 관리에 주의하세요.
4. **시장 시간**: 장 마감 시간에는 일부 API가 정상 응답하지 않을 수 있습니다.

## 버전 정보

- **최초 작성**: 2026-02-11
- **최근 수정**: 2026-02-11
- **호환 API**: KIS Open Trading API v1
- **Python 버전**: 3.8+