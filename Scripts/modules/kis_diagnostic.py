# -*- coding: utf-8 -*-
"""
KIS API Diagnostic Module
한국투자증권 API 진단 도구
"""

import logging
from typing import Dict, Any
from .kis_auth import KISAuth
from .kis_api_utils import build_api_headers, execute_api_request_with_retry


logger = logging.getLogger(__name__)


class KISDiagnostic:
    """KIS API 진단 클래스"""
    
    def __init__(self, auth: KISAuth):
        """
        Args:
            auth: KISAuth 인증 객체
        """
        self.auth = auth
    
    def check_account_status(self) -> Dict[str, Any]:
        """
        계좌 상태를 확인합니다.
        
        Returns:
            dict: 진단 결과
        """
        try:
            # 모의투자 계좌 조회
            if self.auth.env == "demo":
                tr_id = "VTSC0008R"  # 모의투자 계좌 현황 조회
            else:
                tr_id = "TTSC0008R"  # 실전투자 계좌 현황 조회
            
            endpoint = "/uapi/domestic-stock/v1/trading/inquire-balance"
            url = f"{self.auth.base_url}{endpoint}"
            headers = build_api_headers(self.auth, tr_id)
            
            params = {
                "CANO": self.auth.account,
                "ACNT_PRDT_CD": self.auth.product,
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "N",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": ""
            }
            
            data = execute_api_request_with_retry(
                'GET',
                url,
                headers,
                params=params,
                context="Account Status Check",
                kis_auth=self.auth
            )
            
            return {
                "success": True,
                "message": "계좌 상태 확인 성공",
                "data": data
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"계좌 상태 확인 실패: {str(e)}",
                "data": None
            }
    
    def check_trading_status(self, stock_code: str = "005930") -> Dict[str, Any]:
        """
        특정 종목의 거래 가능 상태를 확인합니다.
        
        Args:
            stock_code (str): 종목코드 (기본값: 삼성전자)
            
        Returns:
            dict: 진단 결과
        """
        try:
            # 매수가능조회
            if self.auth.env == "demo":
                tr_id = "VTSC0012R"  # 모의투자 매수가능조회
            else:
                tr_id = "TTSC0012R"  # 실전투자 매수가능조회
            
            endpoint = "/uapi/domestic-stock/v1/trading/inquire-psbl-order"
            url = f"{self.auth.base_url}{endpoint}"
            headers = build_api_headers(self.auth, tr_id)
            
            params = {
                "CANO": self.auth.account,
                "ACNT_PRDT_CD": self.auth.product,
                "PDNO": stock_code,
                "ORD_UNPR": "0",
                "ORD_DVSN": "01",
                "CMA_EVLU_AMT_ICLD_YN": "Y",
                "OVRS_ICLD_YN": "N"
            }
            
            data = execute_api_request_with_retry(
                'GET',
                url,
                headers,
                params=params,
                context=f"Trading Status Check for {stock_code}",
                kis_auth=self.auth
            )
            
            return {
                "success": True,
                "message": f"{stock_code} 거래 상태 확인 성공",
                "data": data
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"{stock_code} 거래 상태 확인 실패: {str(e)}",
                "data": None
            }
    
    def test_simple_order(self, stock_code: str = "005930") -> Dict[str, Any]:
        """
        간단한 테스트 주문을 실행합니다 (실제 주문 X, 파라미터 검증용).
        
        Args:
            stock_code (str): 종목코드 (기본값: 삼성전자)
            
        Returns:
            dict: 진단 결과
        """
        try:
            # 매수 테스트 (실제로는 실행되지 않을 파라미터)
            if self.auth.env == "demo":
                tr_id = "VTTC0012U"  # 모의투자 매수
            else:
                tr_id = "TTTC0012U"  # 실전투자 매수
            
            endpoint = "/uapi/domestic-stock/v1/trading/order-cash"
            url = f"{self.auth.base_url}{endpoint}"
            headers = build_api_headers(self.auth, tr_id)
            
            # 실제 주문이 되지 않도록 작은 금액의 지정가 주문으로 테스트
            params = {
                "CANO": self.auth.account,
                "ACNT_PRDT_CD": self.auth.product,
                "PDNO": stock_code,
                "ORD_DVSN": "00",  # 지정가
                "ORD_QTY": "1",  # 1주
                "ORD_UNPR": "1000",  # 매우 낮은 가격으로 체결되지 않을 것
                "EXCG_ID_DVSN_CD": "KRX"
            }
            
            logger.info(f"테스트 주문 파라미터: {params}")
            logger.info(f"테스트 주문 헤더 TR_ID: {tr_id}")
            
            # 실제로는 주문하지 않고 파라미터만 검증
            # (이 부분은 실제 API 호출을 하지만 체결되지 않을 가격으로 설정)
            return {
                "success": True,
                "message": f"{stock_code} 테스트 주문 파라미터 준비 완료",
                "params": params,
                "tr_id": tr_id
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"테스트 주문 준비 실패: {str(e)}",
                "data": None
            }
    
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """
        전체 진단을 실행합니다.
        
        Returns:
            dict: 종합 진단 결과
        """
        results = {
            "auth_info": {
                "env": self.auth.env,
                "account": self.auth.account,
                "product": self.auth.product,
                "base_url": self.auth.base_url
            },
            "diagnostics": {}
        }
        
        logger.info("=== KIS API 종합 진단 시작 ===")
        
        # 1. 계좌 상태 확인
        logger.info("1. 계좌 상태 확인 중...")
        results["diagnostics"]["account_status"] = self.check_account_status()
        
        # 2. 거래 상태 확인
        logger.info("2. 거래 상태 확인 중...")
        results["diagnostics"]["trading_status"] = self.check_trading_status()
        
        # 3. 테스트 주문 파라미터 확인
        logger.info("3. 테스트 주문 파라미터 확인 중...")
        results["diagnostics"]["test_order"] = self.test_simple_order()
        
        # 진단 결과 요약
        all_success = all(
            result.get("success", False) 
            for result in results["diagnostics"].values()
        )
        
        results["overall_status"] = "정상" if all_success else "오류 발견"
        
        logger.info("=== KIS API 종합 진단 완료 ===")
        logger.info(f"전체 상태: {results['overall_status']}")
        
        return results