# 비트코인 포트폴리오 리밸런싱 통합 가이드

## 개요

이 가이드는 기존 KIS(한국투자증권) 주식/채권 리밸런싱 시스템에 Upbit 비트코인을 통합하는 방법을 설명합니다.

## 변경 사항 요약

### 1. 설정 파일 변경

#### config_basic.json
- `target_weights`에 `coin` 카테고리 추가
- `bitcoin` 티커로 비트코인 목표 비중 설정

```json
{
  "target_weights": {
    "stocks": {
      "005930": 0.35,
      "000660": 0.25,
      "035420": 0.25
    },
    "bonds": {
      "KR103502GA34": 0.0
    },
    "coin": {
      "bitcoin": 0.15
    }
  }
}
```

#### config.json
- `upbit` 키 추가
- 실전 및 데모 환경 API 키 설정

```json
{
    "kis": { ... },
    "upbit": {
        "real": {
            "access_key": "YOUR_UPBIT_ACCESS_KEY",
            "secret_key": "YOUR_UPBIT_SECRET_KEY"
        },
        "demo": {
            "access_key": "DEMO_KEY",
            "secret_key": "DEMO_SECRET",
            "initial_krw_balance": 2000000,
            "initial_btc_balance": 0.0
        }
    }
}
```

### 2. 새로운 모듈

| 모듈 | 설명 |
|------|------|
| `upbit_api_client.py` | Upbit API 호출 및 데모 거래 |
| `unified_portfolio_fetcher.py` | KIS + Upbit 통합 포트폴리오 조회 |

### 3. 수정된 모듈

| 모듈 | 변경 내용 |
|------|----------|
| `config_loader.py` | `get_upbit_config()` 메서드 추가 |
| `rebalancing_engine.py` | bitcoin 주문 생성 로직 추가 |
| `order_executor.py` | bitcoin 주문 실행 로직 추가 |
| `portfolio_rebalancing.py` | 통합 포트폴리오 페처 사용 |

## 동작 방식

### 포트폴리오 스냅샷

```
총 현금 = KIS 현금 + Upbit KRW
총 자산 = 총 현금 + 주식 평가액 + 채권 평가액 + 비트코인 평가액
```

### 리밸런싱 로직

1. **통합 스냅샷 생성**: KIS + Upbit 데이터 통합
2. **목표 비중 계산**: 전체 자산 기준으로 각 자산 목표 금액 계산
3. **주문 생성**: 
   - 주식/채권: 수량 기반 주문
   - 비트코인: 금액 기반 주문
4. **주문 실행**:
   - 주식/채권: KIS API
   - 비트코인: Upbit API (또는 데모 가상 거래)

### 데모 모드 (--demo)

```
┌─────────────────────────────────────────────────────────┐
│                    Demo 모드 동작                        │
├─────────────────────────────────────────────────────────┤
│ KIS:                                                     │
│   - 한국투자증권 모의투자 환경 사용                        │
│   - 실제 모의투자 서버 API 호출                           │
│                                                          │
│ Upbit:                                                   │
│   - 메모리 기반 가상 거래                                 │
│   - 프로세스 종료 시 초기화                               │
│   - 매 시작 시 config의 초기 잔액으로 시작                 │
│   - 비트코인 가격만 실제 API에서 조회                      │
└─────────────────────────────────────────────────────────┘
```

### 실전 모드 (--demo 없이)

```
┌─────────────────────────────────────────────────────────┐
│                    실전 모드 동작                        │
├─────────────────────────────────────────────────────────┤
│ KIS:                                                     │
│   - 실제 주식 계좌 사용                                   │
│   - 실제 매매 주문 실행                                   │
│                                                          │
│ Upbit:                                                   │
│   - 실제 Upbit 계좌 사용                                  │
│   - 실제 비트코인 매매 주문 실행                          │
│   - API 키 필요                                          │
└─────────────────────────────────────────────────────────┘
```

## 사용 방법

### 1. 설정 파일 구성

먼저 `Config/config.json`에 Upbit API 키를 설정합니다.

### 2. 목표 비중 설정

`Config/config_basic.json`에서 비트코인 목표 비중을 설정합니다.

```json
{
  "target_weights": {
    "stocks": {
      "005930": 0.35,   // 삼성전자 35%
      "000660": 0.25,   // SK하이닉스 25%
      "035420": 0.25    // NAVER 25%
    },
    "coin": {
      "bitcoin": 0.15   // 비트코인 15%
    }
  }
}
```

### 3. 실행

```bash
# 데모 모드 단일 실행
python Scripts/apps/portfolio_rebalancing.py --demo --mode once

# 데모 모드 스케줄러 실행
python Scripts/apps/portfolio_rebalancing.py --demo --mode schedule

# 실전 모드 (주의!)
python Scripts/apps/portfolio_rebalancing.py --mode once
```

## 테스트

### Upbit 모듈 테스트

```bash
python Scripts/tests/kis_debug.py --upbit
```

테스트 항목:
1. 비트코인 가격 조회
2. 데모 가상 거래 (매수/매도)
3. 통합 포트폴리오 페처
4. 비트코인 리밸런싱 주문 생성

### 전체 시스템 테스트

```bash
python Scripts/tests/kis_debug.py
```

## 주의사항

1. **실전 모드 사용 시**:
   - Upbit API 키가 올바르게 설정되어 있어야 함
   - 충분한 KRW 잔액 필요 (최소 주문 금액: 5,000원)

2. **데모 모드 특성**:
   - Upbit 비트코인 잔액은 프로세스 종료 시 초기화됨
   - 매 프로세스 시작 시 초기 잔액으로 다시 시작

3. **비트코인 주문**:
   - 금액 기반 주문 (수량이 아닌 KRW 금액 지정)
   - 시장가 주문만 지원

## 파일 구조

```
Investment_Auto/
├── Config/
│   ├── config.json           # KIS + Upbit API 설정
│   └── config_basic.json     # 목표 비중 설정 (coin 카테고리 포함)
├── Scripts/
│   ├── modules/
│   │   ├── upbit_api_client.py         # [신규] Upbit API 클라이언트
│   │   ├── unified_portfolio_fetcher.py # [신규] 통합 포트폴리오 페처
│   │   ├── config_loader.py            # [수정] get_upbit_config() 추가
│   │   ├── rebalancing_engine.py       # [수정] bitcoin 주문 생성
│   │   └── order_executor.py           # [수정] bitcoin 주문 실행
│   ├── apps/
│   │   └── portfolio_rebalancing.py    # [수정] 통합 페처 사용
│   └── tests/
│       └── kis_debug.py                # [수정] Upbit 테스트 추가
└── docs/
    ├── upbit_api_client.md             # [신규] Upbit 모듈 문서
    ├── unified_portfolio_fetcher.md    # [신규] 통합 페처 문서
    └── bitcoin_rebalancing_guide.md    # [신규] 이 문서
```

## 향후 개선 사항

1. **Upbit 주문 타입 확장**: 지정가 주문 지원
2. **다른 암호화폐 지원**: ETH, XRP 등
3. **데모 잔액 영속화**: 파일 또는 DB 저장 옵션
4. **리밸런싱 전략 개선**: 암호화폐 특성 반영

## 관련 문서

- [upbit_api_client.md](upbit_api_client.md)
- [unified_portfolio_fetcher.md](unified_portfolio_fetcher.md)
- [portfolio_rebalancing.md](portfolio_rebalancing.md)
- [rebalancing_engine.md](rebalancing_engine.md)
- [order_executor.md](order_executor.md)
