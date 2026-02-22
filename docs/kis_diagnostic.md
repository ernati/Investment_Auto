# KIS API 진단 도구 (kis_diagnostic.py)

한국투자증권 API 연결 상태와 거래 가능성을 진단하는 모듈입니다. 

## 개요

`kis_diagnostic.py`는 KIS API 관련 문제를 진단하고 해결하기 위한 종합적인 도구를 제공합니다. 특히 주식 거래 실패 문제(`rt_cd=1`, `rt_cd=2` 에러)를 해결하는 데 도움을 줍니다.

## 주요 기능

### 1. 계좌 상태 확인 (`check_account_status`)
- 모의투자/실전투자 계좌 현황 조회
- 계좌 활성화 상태 확인
- 잔고 및 보유 현황 검증

### 2. 거래 상태 확인 (`check_trading_status`)
- 특정 종목의 매수 가능 여부 확인
- 거래 가능 금액 조회
- 주문 제한 사항 확인

### 3. 테스트 주문 파라미터 검증 (`test_simple_order`)
- 실제 주문하지 않고 파라미터만 검증
- TR_ID 및 헤더 구성 확인
- 주문 요청 형식 검증

### 4. 종합 진단 (`run_full_diagnostic`)
- 전체 시스템 상태 점검
- 단계별 진단 결과 제공
- 문제점 자동 식별

## 클래스 구조

```python
class KISDiagnostic:
    def __init__(self, auth: KISAuth)
    def check_account_status(self) -> Dict[str, Any]
    def check_trading_status(self, stock_code: str = "005930") -> Dict[str, Any]
    def test_simple_order(self, stock_code: str = "005930") -> Dict[str, Any]
    def run_full_diagnostic(self) -> Dict[str, Any]
```

## 사용 방법

### 기본 사용법

```python
from modules.kis_auth import KISAuth
from modules.kis_diagnostic import KISDiagnostic

# 인증 초기화 (모의투자)
auth = KISAuth(
    appkey="your_appkey",
    appsecret="your_appsecret", 
    account="50162038",
    env="demo"
)

# 진단 도구 생성
diagnostic = KISDiagnostic(auth)

# 종합 진단 실행
results = diagnostic.run_full_diagnostic()
print(f"전체 상태: {results['overall_status']}")
```

### 개별 진단

```python
# 1. 계좌 상태만 확인
account_result = diagnostic.check_account_status()
if account_result["success"]:
    print("계좌 상태 정상")
else:
    print(f"계좌 문제: {account_result['message']}")

# 2. 삼성전자 거래 가능 여부 확인
trading_result = diagnostic.check_trading_status("005930")
if trading_result["success"]:
    print("삼성전자 거래 가능")

# 3. 주문 파라미터 테스트
order_test = diagnostic.test_simple_order("005930")
print(f"주문 파라미터: {order_test['params']}")
```

## 응답 형식

모든 진단 메서드는 다음과 같은 형식으로 결과를 반환합니다:

```python
{
    "success": bool,           # 진단 성공 여부
    "message": str,           # 결과 메시지
    "data": dict or None      # 상세 데이터 (성공 시)
}
```

### 종합 진단 응답 예시

```python
{
    "auth_info": {
        "env": "demo",
        "account": "50162038", 
        "product": "01",
        "base_url": "https://openapivts.koreainvestment.com:29443"
    },
    "diagnostics": {
        "account_status": {"success": True, "message": "...", "data": {...}},
        "trading_status": {"success": True, "message": "...", "data": {...}},
        "test_order": {"success": True, "message": "...", "params": {...}}
    },
    "overall_status": "정상"  # 또는 "오류 발견"
}
```

## TR_ID 참조표

진단 도구에서 사용하는 TR_ID들:

| 기능 | 실전투자 | 모의투자 | 용도 |
|------|----------|----------|------|
| 계좌 조회 | TTSC0008R | VTSC0008R | 잔고 및 계좌 상태 |
| 매수가능조회 | TTSC0012R | VTSC0012R | 거래 가능 여부 확인 |
| 매수 주문 | TTTC0012U | VTTC0012U | 주문 테스트 |

## 일반적인 에러 해결

### RT_CD=1 (주문 실패)
- 계좌 상태 확인
- 매수 가능 금액 확인
- TR_ID 정확성 검증
- 주문 파라미터 형식 확인

### RT_CD=2 (조회 실패)  
- API 인증 토큰 확인
- 계좌 번호 정확성 검증
- 네트워크 연결 상태 확인

## 명령줄 도구

진단 도구는 독립 실행 가능한 스크립트로도 사용할 수 있습니다:

```bash
cd Investment_Auto/Scripts/apps
python kis_debug.py
```

실행하면 자동으로 종합 진단을 수행하고 결과를 출력합니다.

## 로깅

진단 과정에서 상세한 로그를 출력합니다:

- INFO 레벨: 진단 단계별 진행 상황
- ERROR 레벨: API 에러 및 실패 원인
- DEBUG 레벨: API 요청/응답 상세 정보

## 보안 주의사항

- 진단 결과에는 민감한 계좌 정보가 포함될 수 있습니다
- 로그 파일 공유 시 개인정보 보호에 주의하세요
- API 키 정보는 절대 로깅하지 않습니다

## 관련 모듈

- `kis_auth.py`: API 인증 관리
- `kis_api_utils.py`: API 호출 유틸리티
- `kis_trading.py`: 실제 거래 실행
- `kis_debug.py`: 명령줄 진단 도구