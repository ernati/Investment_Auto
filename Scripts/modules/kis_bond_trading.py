# -*- coding: utf-8 -*-
"""
KIS Bond Trading Module
한국투자증권 Open Trading API 장내채권 거래(매수/매도) 모듈
"""

import requests
import pandas as pd
from typing import Optional, Dict, Any


class KISBondTrading:
    """한국투자증권 API 장내채권 거래 클래스"""
    
    def __init__(self, auth):
        """
        Args:
            auth: KISAuth 인증 객체
        """
        self.auth = auth
    
    def _call_api(self, endpoint, tr_id, params=None, method='POST'):
        """API를 호출합니다.
        
        Args:
            endpoint (str): API 엔드포인트
            tr_id (str): 거래ID
            params (dict): 요청 파라미터
            method (str): HTTP 메서드 ('GET' 또는 'POST')
            
        Returns:
            dict: API 응답
        """
        url = f"{self.auth.base_url}{endpoint}"
        headers = self.auth.get_headers(tr_id)
        
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        else:  # POST
            response = requests.post(url, headers=headers, json=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"API 호출 실패: {response.status_code} - {response.text}"
            raise Exception(error_msg)
    
    def order_bond(
        self,
        bond_code: str,
        order_type: str,
        quantity: int,
        price: str,
        samt_mket_ptci_yn: str = "N",
        bond_rtl_mket_yn: str = "Y"
    ) -> Dict[str, Any]:
        """장내채권 주문을 실행합니다.
        
        Args:
            bond_code (str): 채권코드 (예: "KR6095572D81")
            order_type (str): 주문유형 ("buy": 매수, "sell": 매도)
            quantity (int): 주문수량
            price (str): 채권주문단가
            samt_mket_ptci_yn (str): 동시시장참여여부 (기본값: "N")
            bond_rtl_mket_yn (str): 채권소매시장여부 (기본값: "Y")
            
        Returns:
            dict: 주문 결과
                - success (bool): 성공 여부
                - order_no (str): 주문번호
                - message (str): 결과 메시지
                - data (dict): 원본 응답 데이터
                
        Raises:
            ValueError: 잘못된 파라미터 입력 시
            Exception: API 호출 실패 시
        """
        # 파라미터 검증
        if order_type not in ["buy", "sell"]:
            raise ValueError("order_type은 'buy' 또는 'sell'이어야 합니다.")
        
        if quantity <= 0:
            raise ValueError("quantity는 0보다 커야 합니다.")
        
        # TR_ID 설정 (환경에 따라 자동 변환)
        if self.auth.env == "real":
            # 실전투자용 TR ID
            if order_type == "buy":
                tr_id = "TTTC0952U"  # 실전투자 채권 매수
            else:  # sell
                tr_id = "TTTC0958U"  # 실전투자 채권 매도
        else:  # demo
            # 모의투자용 TR ID
            if order_type == "buy":
                tr_id = "VTTC0952U"  # 모의투자 채권 매수
            else:  # sell
                tr_id = "VTTC0958U"  # 모의투자 채권 매도
        
        # API 엔드포인트
        if order_type == "buy":
            endpoint = "/uapi/domestic-bond/v1/trading/buy"
        else:
            endpoint = "/uapi/domestic-bond/v1/trading/sell"
        
        # 요청 파라미터 구성 (대문자 키 사용)
        params = {
            "CANO": self.auth.account,           # 종합계좌번호
            "ACNT_PRDT_CD": self.auth.product,   # 계좌상품코드
            "PDNO": bond_code,                   # 상품번호(채권코드)
            "ORD_QTY2": str(quantity),           # 주문수량
            "BOND_ORD_UNPR": price,              # 채권주문단가
            "SAMT_MKET_PTCI_YN": samt_mket_ptci_yn,  # 동시시장참여여부
            "BOND_RTL_MKET_YN": bond_rtl_mket_yn,    # 채권소매시장여부
        }
        
        # 매도 시 추가 파라미터
        if order_type == "sell":
            # 매도 주문에만 필요한 추가 파라미터들
            params.update({
                "ORD_DVSN": "01",                    # 주문구분 (시장가)
                "SPRX_YN": "N",                      # 주식분할여부
                "SLL_AGCO_OPPS_SLL_YN": "N",         # 매도유가대상매도여부
                "BUY_DT": "",                        # 매수일자 (공백 가능)
                "BUY_SEQ": "",                       # 매수순번 (공백 가능)
            })
        
        # 공통 선택적 파라미터
        params.update({
            "IDCR_STFNO": "",                    # 투자상담사번호
            "MGCO_APTM_ODNO": "",                # 운용사지정주문번호
            "ORD_SVR_DVSN_CD": "",               # 주문서버구분코드
            "CTAC_TLNO": "",                     # 연락전화번호
        })
        
        try:
            # API 호출
            response = self._call_api(endpoint, tr_id, params, method='POST')
            
            # 응답 처리
            if response['rt_cd'] == '0':
                # 성공
                output = response.get('output', {})
                result = {
                    'success': True,
                    'order_no': output.get('ODNO', ''),  # 주문번호
                    'order_time': output.get('ORD_TMD', ''),  # 주문시각
                    'message': response.get('msg1', '채권 주문이 정상적으로 처리되었습니다.'),
                    'data': response
                }
                return result
            else:
                # 실패
                result = {
                    'success': False,
                    'order_no': '',
                    'message': response.get('msg1', '채권 주문 처리 중 오류가 발생했습니다.'),
                    'data': response
                }
                return result
                
        except Exception as e:
            # 예외 발생
            result = {
                'success': False,
                'order_no': '',
                'message': f"채권 주문 중 오류 발생: {str(e)}",
                'data': {}
            }
            return result
    
    def buy_bond(self, bond_code: str, quantity: int, price: str) -> Dict[str, Any]:
        """채권 매수 주문을 실행합니다.
        
        Args:
            bond_code (str): 채권코드 (예: "KR6095572D81")
            quantity (int): 주문수량
            price (str): 채권주문단가
            
        Returns:
            dict: 주문 결과
        """
        return self.order_bond(
            bond_code=bond_code,
            order_type="buy",
            quantity=quantity,
            price=price
        )
    
    def sell_bond(self, bond_code: str, quantity: int, price: str) -> Dict[str, Any]:
        """채권 매도 주문을 실행합니다.
        
        Args:
            bond_code (str): 채권코드 (예: "KR6095572D81")
            quantity (int): 주문수량
            price (str): 채권주문단가
            
        Returns:
            dict: 주문 결과
        """
        return self.order_bond(
            bond_code=bond_code,
            order_type="sell", 
            quantity=quantity,
            price=price
        )
    
    def get_bond_info(self, bond_code: str, prdt_type_cd: str = "302") -> Dict[str, Any]:
        """채권 기본 정보를 조회합니다.
        
        Args:
            bond_code (str): 채권코드 (예: "KR6095572D81")
            prdt_type_cd (str): 상품유형코드 (기본값: "302")
            
        Returns:
            dict: 채권 정보
        """
        # 모의투자에서는 채권 기본 정보 조회가 지원되지 않으므로 현재가 조회로 대체
        if self.auth.env == "demo":
            return self.get_bond_price(bond_code)
        
        # TR_ID는 실전투자/모의투자 구분 없음
        tr_id = "CTPF1114R"
        endpoint = "/uapi/domestic-bond/v1/quotations/search-bond-info"
        
        params = {
            "PDNO": bond_code,
            "PRDT_TYPE_CD": prdt_type_cd,
        }
        
        try:
            response = self._call_api(endpoint, tr_id, params)
            
            if response['rt_cd'] == '0':
                return {
                    'success': True,
                    'data': response.get('output', {}),
                    'message': '채권 정보 조회 성공'
                }
            else:
                return {
                    'success': False,
                    'data': {},
                    'message': response.get('msg1', '채권 정보 조회 실패')
                }
                
        except Exception as e:
            return {
                'success': False,
                'data': {},
                'message': f"채권 정보 조회 중 오류 발생: {str(e)}"
            }
    
    def get_bond_price(self, bond_code: str, market_div_code: str = "B") -> Dict[str, Any]:
        """채권 현재가 정보를 조회합니다.
        
        Args:
            bond_code (str): 채권코드 (예: "KR6095572D81")
            market_div_code (str): 조건시장분류코드 (기본값: "B")
            
        Returns:
            dict: 채권 현재가 정보
        """
        tr_id = "FHKBJ773400C0"
        endpoint = "/uapi/domestic-bond/v1/quotations/inquire-price"
        
        params = {
            "FID_COND_MRKT_DIV_CODE": market_div_code,
            "FID_INPUT_ISCD": bond_code,
        }
        
        try:
            response = self._call_api(endpoint, tr_id, params, method='GET')
            
            if response['rt_cd'] == '0':
                output_data = response.get('output', {})
                return {
                    'success': True,
                    'data': output_data,
                    'message': '채권 현재가 조회 성공'
                }
            else:
                return {
                    'success': False,
                    'data': {},
                    'message': response.get('msg1', '채권 현재가 조회 실패')
                }
                
        except Exception as e:
            return {
                'success': False,
                'data': {},
                'message': f"채권 현재가 조회 중 오류 발생: {str(e)}"
            }