# -*- coding: utf-8 -*-
"""
KIS API Portfolio Data Module
한국투자증권 Open API를 통해 포트폴리오 데이터를 조회하는 모듈
- 계좌 잔고 조회
- 보유종목 조회
- 가격 데이터 조회
"""

import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

import pandas as pd
from .demo_cash_manager import get_demo_cash_manager

from .kis_auth import KISAuth
from .portfolio_models import PortfolioSnapshot, PositionSnapshot, PriceSnapshot
from .kis_api_utils import build_api_headers, validate_api_response, execute_api_request_with_retry


logger = logging.getLogger(__name__)


class KISPortfolioFetcher:
    """KIS API를 통해 포트폴리오 데이터를 조회하는 클래스"""
    
    def __init__(self, kis_auth: KISAuth):
        """
        Args:
            kis_auth (KISAuth): 인증 정보를 담은 KISAuth 인스턴스
        """
        self.kis_auth = kis_auth
        self.base_url = kis_auth.base_url
        
    def fetch_account_balance(self) -> Dict[str, float]:
        """
        계좌 잔고를 조회합니다.
        모의투자 환경에서는 가상 현금 관리자를 통해 잔액을 조회합니다.
        
        Returns:
            {
                'cash': 현금잔고,
                'd2_cash': D2 현금,
                'orderable_cash': 주문가능현금,
                ...
            }
        """
        # 모의투자 환경에서는 가상 현금 관리자를 사용
        if self.kis_auth.env == "demo":
            try:
                demo_manager = get_demo_cash_manager(self.kis_auth.account)
                cash_balance = demo_manager.get_cash_balance()
                logger.info(f"Demo 환경 현금 잔고 조회: {cash_balance:,}원")
                
                return {
                    'cash': cash_balance,
                    'd2_cash': cash_balance,  # 모의투자에서는 같은 값
                    'orderable_cash': cash_balance,  # 모의투자에서는 같은 값
                    'total_cash': cash_balance
                }
            except Exception as e:
                logger.error(f"Demo 현금 잔고 조회 실패: {e}")
                # 에러 시 기본값 반환
                return {'cash': 10000000.0, 'd2_cash': 10000000.0, 'orderable_cash': 10000000.0, 'total_cash': 10000000.0}
        
        # 실전 환경에서는 실제 API 호출
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        
        # TR_ID 설정 (환경별 정규화는 build_api_headers에서 자동 처리)
        tr_id = 'TTTC8434R'
        headers = build_api_headers(self.kis_auth, tr_id)
        
        # open-trading-api 표준 파라미터 구조 사용
        params = {
            "CANO": self.kis_auth.account[:8],
            "ACNT_PRDT_CD": self.kis_auth.product,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "01",  # 01=대출일별, 02=종목별
            "UNPR_DVSN": "01",  # 단가구분
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",  # 01=전일매매미포함 (테스트 성공 파라미터)
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        try:
            data = execute_api_request_with_retry(
                'GET',
                url,
                headers,
                params=params,
                context='Fetch account balance',
                kis_auth=self.kis_auth
            )
            
            # 응답 데이터 파싱
            # output2[0]에 계좌 전체 정보가 들어있음
            output2 = data.get('output2', [])
            if not output2:
                logger.warning("No account balance data in response")
                return {'cash': 0.0, 'd2_cash': 0.0, 'orderable_cash': 0.0}
            
            account_info = output2[0]
            logger.info(f"Account balance fetched successfully: {data.get('msg1', '')}")
            
            return {
                'cash': float(account_info.get('dnca_tot_amt', 0)),  # 예수금총금액
                'd2_cash': float(account_info.get('d2_deposit', 0)),  # D+2 예수금
                'orderable_cash': float(account_info.get('nxdy_excc_amt', 0)),  # 익일정산금액
            }
                
        except Exception as e:
            logger.error(f"Account balance fetch failed: {e}")
            logger.info("Using fallback method: fetching balance via holdings API")
            # 대체 방법: 보유종목 조회를 통해 계좌 정보 획득
            return self._fetch_balance_via_holdings()
    
    def fetch_holdings(self) -> Dict[str, int]:
        """
        보유종목과 수량을 조회합니다.
        
        Returns:
            {
                'ticker1': 수량,
                'ticker2': 수량,
                ...
            }
        """
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
        
        # TR_ID 설정 (환경별 정규화는 build_api_headers에서 자동 처리)
        tr_id = 'TTTC8434R'
        headers = build_api_headers(self.kis_auth, tr_id)
        
        params = {
            'CANO': self.kis_auth.account[:8],  # 종합계좌번호
            'ACNT_PRDT_CD': self.kis_auth.product,  # 계좌상품코드
            'AFHR_FLPR_YN': 'N',  # 시간외단일가여부
            'OFL_YN': '',  # 오프라인여부
            'INQR_DVSN': '01',  # 조회구분 (01=대출일별, 02=종목별)
            'UNPR_DVSN': '01',  # 단가구분
            'FUND_STTL_ICLD_YN': 'N',  # 펀드결제포함여부
            'FNCG_AMT_AUTO_RDPT_YN': 'N',  # 융자금액자동상환여부
            'PRCS_DVSN': '00',  # 처리구분 (00=전일매매포함, 01=전일매매미포함)
            'CTX_AREA_FK100': '',  # 연속조회검색조건100
            'CTX_AREA_NK100': '',  # 연속조회키100
        }
        
        data = execute_api_request_with_retry(
            'GET',
            url,
            headers,
            params=params,
            context='Fetch holdings',
            kis_auth=self.kis_auth
        )
        
        holdings = {}
        # output1에 보유 종목 리스트가 들어있음
        output1_list = data.get('output1', [])
        
        for item in output1_list:
            ticker = item.get('pdno', '').strip()  # 상품번호 (종목코드)
            quantity = int(item.get('hldg_qty', 0))  # 보유수량
            
            if ticker and quantity > 0:
                holdings[ticker] = quantity
        
        logger.info(f"Holdings fetched: {len(holdings)} tickers")
        return holdings
    
    def _fetch_balance_via_holdings(self) -> Dict[str, float]:
        """
        보유종목 조회 API를 통해 계좌 잔고 정보를 획득하는 대체 방법
        테스트에서 성공한 TTTC8434R 방식 사용
        
        Returns:
            Dict[str, float]: 계좌 잔고 정보
        """
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            
            # TR_ID 설정 (환경별 정규화는 build_api_headers에서 자동 처리)
            tr_id = 'TTTC8434R'
            headers = build_api_headers(self.kis_auth, tr_id)
            
            params = {
                "cano": self.kis_auth.account[:8],
                "acnt_prdt_cd": self.kis_auth.product,
                "afhr_flpr_yn": "N",
                "unpr": "",
                "fund_sttl_icld_yn": "N",
                "fncg_ami_auto_rdpt_yn": "N", 
                "prcs_dvsn": "01",
                "cost_icld_yn": "N",
                "ctx_area_fk100": "",
                "ctx_area_nk100": ""
            }
            
            data = execute_api_request_with_retry(
                'GET',
                url,
                headers,
                params=params,
                context='Fetch balance via holdings API',
                kis_auth=self.kis_auth
            )
            
            output2 = data.get('output2', [])
            if not output2:
                logger.error("No account data available from holdings API")
                return {'cash': 0.0, 'd2_cash': 0.0, 'orderable_cash': 0.0}
            
            account_info = output2[0]
            logger.info("Successfully retrieved balance via holdings API fallback")
            
            return {
                'cash': float(account_info.get('dnca_tot_amt', 0)),
                'd2_cash': float(account_info.get('d2_deposit', 0)),
                'orderable_cash': float(account_info.get('nxdy_excc_amt', 0)),
            }
            
        except Exception as e:
            logger.error(f"Fallback balance fetch also failed: {e}")
            return {'cash': 0.0, 'd2_cash': 0.0, 'orderable_cash': 0.0}
    
    def fetch_current_price(self, ticker: str, max_retries: int = 3) -> float:
        """
        종목의 현재가를 조회합니다.
        
        Args:
            ticker (str): 종목코드 (주식 또는 채권)
            max_retries (int): 최대 재시도 횟수
            
        Returns:
            float: 현재가
        """
        # 채권 코드 판별 (KR로 시작하고 길이가 12자리인 경우)
        is_bond = ticker.startswith('KR') and len(ticker) == 12
        
        if is_bond:
            return self._fetch_bond_price(ticker, max_retries)
        else:
            return self._fetch_stock_price(ticker, max_retries)
    
    def _fetch_stock_price(self, ticker: str, max_retries: int = 3) -> float:
        """주식 현재가 조회"""
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = build_api_headers(self.kis_auth, 'FHKST01010100')
        
        params = {
            'FID_COND_MRKT_DIV_CODE': 'J',  # 주식
            'FID_INPUT_ISCD': ticker,
        }
        
        last_error = None
        for attempt in range(max_retries):
            try:
                data = execute_api_request_with_retry(
                    'GET',
                    url,
                    headers,
                    params=params,
                    context=f'Fetch stock price for {ticker} (attempt {attempt + 1})',
                    kis_auth=self.kis_auth,
                    max_retries=1
                )
                
                output = data.get('output', {})
                price = float(output.get('stck_prpr', 0))  # 주식 현재가
                
                if price > 0:
                    logger.debug(f"Stock price fetched for {ticker}: {price}")
                    return price
                else:
                    logger.warning(f"Zero stock price returned for {ticker} on attempt {attempt + 1}")
                    
            except Exception as e:
                last_error = e
                error_msg = str(e)
                if isinstance(e, RuntimeError) and "KIS API error" in error_msg:
                    if " - " in error_msg:
                        error_msg = error_msg.split(" - ", 1)[1]
                
                logger.warning(f"Stock price fetch failed for {ticker} on attempt {attempt + 1}: {error_msg}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(0.5)
                    
        final_error_msg = str(last_error)
        if isinstance(last_error, RuntimeError) and "KIS API error" in final_error_msg:
            if " - " in final_error_msg:
                final_error_msg = final_error_msg.split(" - ", 1)[1]
        
        logger.error(f"Failed to fetch stock price for {ticker} after {max_retries} attempts: {final_error_msg}")
        return 0.0

    def _fetch_bond_price(self, ticker: str, max_retries: int = 3) -> float:
        """채권 현재가 조회"""
        url = f"{self.base_url}/uapi/domestic-bond/v1/quotations/inquire-price"
        headers = build_api_headers(self.kis_auth, 'FHKBJ773400C0')
        
        params = {
            'FID_COND_MRKT_DIV_CODE': 'B',  # 채권
            'FID_INPUT_ISCD': ticker,
        }
        
        last_error = None
        for attempt in range(max_retries):
            try:
                data = execute_api_request_with_retry(
                    'GET',
                    url,
                    headers,
                    params=params,
                    context=f'Fetch bond price for {ticker} (attempt {attempt + 1})',
                    kis_auth=self.kis_auth,
                    max_retries=1
                )
                
                output = data.get('output', {})
                # 채권은 stck_prpr이 아닌 bond_prpr 또는 현재가 필드명 사용
                price = float(output.get('bond_prpr', 0)) or float(output.get('stck_prpr', 0))
                
                if price > 0:
                    logger.debug(f"Bond price fetched for {ticker}: {price}")
                    return price
                else:
                    logger.warning(f"Zero bond price returned for {ticker} on attempt {attempt + 1}")
                    logger.debug(f"Bond API response output fields: {list(output.keys())}")
                    
            except Exception as e:
                last_error = e
                error_msg = str(e)
                if isinstance(e, RuntimeError) and "KIS API error" in error_msg:
                    if " - " in error_msg:
                        error_msg = error_msg.split(" - ", 1)[1]
                
                logger.warning(f"Bond price fetch failed for {ticker} on attempt {attempt + 1}: {error_msg}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(0.5)
                    
        final_error_msg = str(last_error)
        if isinstance(last_error, RuntimeError) and "KIS API error" in final_error_msg:
            if " - " in final_error_msg:
                final_error_msg = final_error_msg.split(" - ", 1)[1]
        
        logger.error(f"Failed to fetch bond price for {ticker} after {max_retries} attempts: {final_error_msg}")
        return 0.0
    
    def fetch_multiple_prices(self, tickers: List[str]) -> Dict[str, float]:
        """
        여러 종목의 현재가를 조회합니다.
        
        Args:
            tickers (List[str]): 종목코드 리스트
            
        Returns:
            {ticker: price, ...}
        """
        prices = {}

        if not tickers:
            return prices
        
        for ticker in dict.fromkeys(tickers):
            try:
                price = self.fetch_current_price(ticker)
                prices[ticker] = price
            except Exception as e:
                logger.warning(f"Failed to fetch price for {ticker}: {e}")
                # 하나의 조회 실패가 전체를 중단하지 않도록
                continue
        
        return prices
    
    def fetch_portfolio_snapshot(
        self,
        portfolio_id: str,
        price_source: str = "last",
        extra_tickers: Optional[List[str]] = None
    ) -> PortfolioSnapshot:
        """
        포트폴리오의 현재 상태를 스냅샷으로 반환합니다.
        
        Args:
            portfolio_id (str): 포트폴리오 ID
            price_source (str): 가격 출처 ("last" 또는 "close")
            
        Returns:
            PortfolioSnapshot: 포트폴리오 스냅샷
        """
        logger.info(f"Fetching portfolio snapshot for {portfolio_id}")
        
        # 1) 계좌 잔고 조회 (현금 포함)
        balance_info = self.fetch_account_balance()
        cash = balance_info.get('orderable_cash', 0)
        
        # 2) 보유종목 조회
        holdings = self.fetch_holdings()
        
        # 3) 각 종목의 현재가 조회
        tickers_to_price = list(holdings.keys())
        if extra_tickers:
            tickers_to_price.extend(extra_tickers)

        prices = self.fetch_multiple_prices(tickers_to_price)
        
        # 4) PortfolioSnapshot 생성
        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio_id,
            timestamp=datetime.now(),
            cash=cash
        )
        
        for ticker, quantity in holdings.items():
            price = prices.get(ticker, 0)
            snapshot.add_position(ticker, quantity, price)

        if extra_tickers:
            for ticker in extra_tickers:
                if ticker in snapshot.positions:
                    continue
                price = prices.get(ticker, 0)
                snapshot.add_position(ticker, 0, price)
        
        logger.info(
            f"Portfolio snapshot created: "
            f"cash={snapshot.cash:.2f}, "
            f"stocks_value={snapshot.stocks_value:.2f}, "
            f"total_value={snapshot.total_value:.2f}"
        )
        
        return snapshot
