# KIS Portfolio Fetcher Module Update (2026-02-18)

## 개요
한국투자증권(KIS) Open API를 통해 포트폴리오 데이터를 조회하는 모듈에 대한 2026년 2월 18일 수정 사항 및 버그 수정 내용입니다.

## 주요 수정 사항

### 1. 계정 잔고 조회 파라미터 수정 (OPSQ2000 오류 해결)

**문제점**: 
- `fetch_account_balance()` 함수에서 소문자 파라미터를 사용하여 API 호출 실패
- `[OPSQ2000] ERROR : INPUT INVALID_CHECK_ACNO` 오류 발생

**해결 방법**:
```python
# 수정 전 (소문자 파라미터)
params = {
    "cano": self.kis_auth.account[:8],
    "acnt_prdt_cd": self.kis_auth.product,
    "afhr_flpr_yn": "N",
    # ...
}

# 수정 후 (대문자 파라미터 - open-trading-api 표준)
params = {
    "CANO": self.kis_auth.account[:8],
    "ACNT_PRDT_CD": self.kis_auth.product,
    "AFHR_FLPR_YN": "N",
    # ...
}
```

**참고**: open-trading-api 저장소의 표준 파라미터 형식을 따라 대문자로 통일

### 2. 채권 가격 조회 기능 구현

**문제점**:
- 채권(KR103502GA34)을 주식으로 처리하여 가격 조회 실패
- 주식용 API 엔드포인트에 채권 코드를 요청하여 0원 반환

**해결 방법**:
```python
def fetch_current_price(self, ticker: str, max_retries: int = 3) -> float:
    """종목코드에 따라 주식/채권을 구분하여 가격 조회"""
    # 채권 코드 판별 (KR로 시작하고 길이가 12자리)
    is_bond = ticker.startswith('KR') and len(ticker) == 12
    
    if is_bond:
        return self._fetch_bond_price(ticker, max_retries)
    else:
        return self._fetch_stock_price(ticker, max_retries)
```

**주식 가격 조회**:
- 엔드포인트: `/uapi/domestic-stock/v1/quotations/inquire-price`
- TR_ID: `FHKST01010100`
- 시장분류코드: `'J'` (주식)

**채권 가격 조회**:
- 엔드포인트: `/uapi/domestic-bond/v1/quotations/inquire-price`
- TR_ID: `FHKBJ773400C0`
- 시장분류코드: `'B'` (채권)

### 3. 파라미터 표준화

**기존 문제점**:
- `fetch_account_balance()`와 `fetch_holdings()` 함수에서 서로 다른 파라미터 형식 사용
- 일부는 소문자, 일부는 대문자로 inconsistent

**해결책**:
- 모든 API 파라미터를 open-trading-api 표준에 맞게 대문자로 통일
- 파라미터 이름도 공식 API 문서와 일치시킴

## 수정된 함수들

### 1. `fetch_account_balance()`
```python
def fetch_account_balance(self) -> Dict[str, float]:
    """계좌 잔고를 조회합니다."""
    # 표준 파라미터 형식으로 수정
    params = {
        "CANO": self.kis_auth.account[:8],
        "ACNT_PRDT_CD": self.kis_auth.product,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "01",
        "UNPR_DVSN": "01", 
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
```

### 2. `_fetch_stock_price()` (신규)
```python
def _fetch_stock_price(self, ticker: str, max_retries: int = 3) -> float:
    """주식 현재가 조회 전용 함수"""
    url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
    headers = build_api_headers(self.kis_auth, 'FHKST01010100')
    params = {
        'FID_COND_MRKT_DIV_CODE': 'J',  # 주식
        'FID_INPUT_ISCD': ticker,
    }
```

### 3. `_fetch_bond_price()` (신규)
```python
def _fetch_bond_price(self, ticker: str, max_retries: int = 3) -> float:
    """채권 현재가 조회 전용 함수"""
    url = f"{self.base_url}/uapi/domestic-bond/v1/quotations/inquire-price"
    headers = build_api_headers(self.kis_auth, 'FHKBJ773400C0')
    params = {
        'FID_COND_MRKT_DIV_CODE': 'B',  # 채권
        'FID_INPUT_ISCD': ticker,
    }
```

## 테스트 방법

수정된 기능들은 `Scripts/apps/kis_debug.py`로 테스트할 수 있습니다:

```bash
# 디버그 모드로 테스트 실행
python Scripts/apps/kis_debug.py
```

테스트 항목:
- ✅ 계정 잔고 조회
- ✅ 주식 가격 조회 (삼성전자)
- ✅ 채권 가격 조회 (KR103502GA34)
- ✅ 보유종목 조회

## 예상 효과

1. **OPSQ2000 오류 해결**: 계정 잔고 조회가 정상 작동
2. **채권 가격 조회 성공**: 포트폴리오에서 채권 정보 정상 표시
3. **API 호환성 향상**: open-trading-api 표준과 완전 호환
4. **리밸런싱 기능 정상화**: 현재가 조회 실패로 인한 리밸런싱 스킵 문제 해결

## 관련 파일들

- `Scripts/modules/kis_portfolio_fetcher.py` (수정됨)
- `Scripts/apps/kis_debug.py` (테스트 코드 추가)
- `Config/config.json` (KIS API 설정)

## 주의사항

- 채권은 장이 열리지 않는 시간대에는 가격이 0으로 반환될 수 있음
- 모의투자 환경에서는 일부 채권 종목의 실시간 가격이 제공되지 않을 수 있음
- 파라미터 형식은 향후 API 업데이트 시에도 대문자 표준을 유지해야 함