# Upbit API Client Module (upbit_api_client.py)

## 개요

Upbit Open API를 통해 비트코인 거래를 수행하는 모듈입니다. 한국투자증권(KIS) 주식과 함께 포트폴리오 리밸런싱에 비트코인을 포함할 수 있도록 지원합니다.

## 주요 기능

- **계좌 잔고 조회**: KRW 및 BTC 잔고 조회
- **비트코인 현재가 조회**: KRW-BTC 마켓 시세 조회
- **비트코인 매수/매도**: 시장가 주문 지원
- **데모 모드 지원**: 실제 API 호출 없이 메모리상 가상 거래

## 클래스

### UpbitAuth

Upbit API 인증 정보 관리 클래스입니다.

```python
from modules.upbit_api_client import UpbitAuth

auth = UpbitAuth(
    access_key="YOUR_ACCESS_KEY",
    secret_key="YOUR_SECRET_KEY",
    env="demo"  # 또는 "real"
)
```

### DemoUpbitCashManager

데모 모드용 가상 현금/비트코인 관리 클래스입니다. 프로세스 메모리 내에서만 유지되며, 프로세스 종료 시 초기화됩니다.

```python
from modules.upbit_api_client import DemoUpbitCashManager

manager = DemoUpbitCashManager(
    initial_krw=2000000.0,  # 초기 KRW 잔액 (기본: 200만원)
    initial_btc=0.0          # 초기 BTC 잔액 (기본: 0)
)

# 잔액 조회
balances = manager.get_balances()
print(f"KRW: {balances['krw']:,}, BTC: {balances['btc']:.8f}")

# 가상 매수
result = manager.buy(100000, 95000000)  # 10만원으로 BTC 매수 (가격 9500만원)

# 가상 매도
result = manager.sell(0.001, 95500000)  # 0.001 BTC 매도 (가격 9550만원)
```

### UpbitClient

실제 API 호출 또는 데모 거래를 수행하는 메인 클라이언트입니다.

```python
from modules.upbit_api_client import UpbitClient, UpbitAuth

auth = UpbitAuth("access_key", "secret_key", "demo")
client = UpbitClient(auth)

# 비트코인 가격 조회
price = client.get_bitcoin_price()
print(f"BTC 현재가: {price['trade_price']:,} KRW")

# 계좌 정보 조회
account = client.get_account_info()
print(f"KRW 잔액: {account['krw']:,}")

# 비트코인 매수
result = client.buy_bitcoin(100000)  # 10만원 매수

# 비트코인 매도
result = client.sell_bitcoin()  # 전량 매도
```

## 전역 함수

### get_upbit_client

전역 Upbit 클라이언트 인스턴스를 가져옵니다.

```python
from modules.upbit_api_client import get_upbit_client

# Demo 모드
client = get_upbit_client("demo")

# 실전 모드
client = get_upbit_client("real")

# 강제 재생성
client = get_upbit_client("demo", reload=True)
```

## 설정

### config.json

`Config/config.json` 파일에 Upbit API 키를 설정합니다:

```json
{
    "kis": { ... },
    "upbit": {
        "real": {
            "access_key": "YOUR_UPBIT_ACCESS_KEY",
            "secret_key": "YOUR_UPBIT_SECRET_KEY"
        },
        "demo": {
            "access_key": "DEMO_UPBIT_ACCESS_KEY",
            "secret_key": "DEMO_UPBIT_SECRET_KEY",
            "initial_krw_balance": 2000000,
            "initial_btc_balance": 0.0
        }
    }
}
```

## 데모 모드 동작

데모 모드(`env="demo"`)에서는:

1. **실제 API 미호출**: Upbit API를 호출하지 않습니다.
2. **메모리 기반 거래**: 가상 잔액이 메모리 내에서 관리됩니다.
3. **비트코인 가격은 실제 조회**: 가격 정보는 실제 API에서 가져옵니다.
4. **프로세스 종료 시 초기화**: 데모 잔액은 프로세스 종료 시 사라집니다.

이 동작은 요구사항에 따라 의도적으로 설계되었습니다:
- Upbit은 모의투자 환경을 제공하지 않음
- 매번 프로세스 시작 시 초기 자금으로 리밸런싱 시작

## 에러 처리

API 호출 실패 시 다음 형식의 딕셔너리가 반환됩니다:

```python
{
    "success": False,
    "error": "에러 메시지"
}
```

성공 시에는 `"success": True`와 함께 해당 데이터가 반환됩니다.

## 수수료

- **기본 수수료율**: 0.05% (업비트 기본 수수료)
- **데모 모드에서도 동일한 수수료 적용**: 실전과 동일한 환경 시뮬레이션

## 관련 모듈

- [config_loader.py](config_loader.md): 설정 파일 로드
- [unified_portfolio_fetcher.py](unified_portfolio_fetcher.md): KIS + Upbit 통합 포트폴리오 조회
- [order_executor.py](order_executor.md): 주문 실행 (비트코인 포함)
- [rebalancing_engine.py](rebalancing_engine.md): 리밸런싱 계획 생성

## 테스트

```bash
# Upbit 관련 테스트만 실행
python Scripts/tests/kis_debug.py --upbit
```
