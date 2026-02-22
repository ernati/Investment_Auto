# -*- coding: utf-8 -*-
"""
KIS Trading Module
한국투자증권 Open Trading API 거래(매수/매도) 모듈
"""

import logging
import pandas as pd
from typing import Optional, Dict, Any

from .kis_api_utils import execute_api_request_with_retry, build_api_headers


logger = logging.getLogger(__name__)


class KISTrading:
    """한국투자증권 API 거래 클래스"""
    
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
        headers = build_api_headers(self.auth, tr_id)
        
        try:
            response_data = execute_api_request_with_retry(
                method=method,
                url=url,
                headers=headers,
                params=params if method == 'GET' else None,
                json_data=params if method == 'POST' else None,
                context=f"KIS Trading API ({tr_id})",
                kis_auth=self.auth
            )
            return response_data
        except Exception as e:
            raise Exception(f"API 호출 실패: {str(e)}")
    
    def order_cash(
        self,
        stock_code: str,
        order_type: str,
        quantity: int,
        price: str = "0",
        order_division: str = "01",
        excg_id_dvsn_cd: str = "KRX"  # 모의투자는 KRX만 가능
    ) -> Dict[str, Any]:
        """현금 주식 주문을 실행합니다.
        
        Args:
            stock_code (str): 종목코드 (예: "005930")
            order_type (str): 주문유형 ("buy": 매수, "sell": 매도)
            quantity (int): 주문수량
            price (str): 주문단가 (기본값: "0" - 시장가)
            order_division (str): 주문구분 (기본값: "01" - 시장가)
                - "00": 지정가
                - "01": 시장가
                - "02": 조건부지정가
                - "03": 최유리지정가
                - "04": 최우선지정가
                - "05": 장전시간외
                - "06": 장후시간외
                - "07": 시간외단일가
                - "08": 자기주식
                - "09": 자기주식S-Option
                - "10": 자기주식금전신탁
                - "11": IOC지정가
                - "12": FOK지정가
                - "13": IOC시장가
                - "14": FOK시장가
                - "15": IOC최유리
                - "16": FOK최유리
            excg_id_dvsn_cd (str): 거래소ID구분코드 (기본값: "SOR")
                - "SOR": Smart Order Routing
                - "KRX": 한국거래소
                - "NXT": NASDAQ
            
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
            # 실전투자용 TR ID (신버전)
            if order_type == "buy":
                tr_id = "TTTC0012U"  # 실전투자 매수 (신버전)
            else:  # sell
                tr_id = "TTTC0011U"  # 실전투자 매도 (신버전)
        else:  # demo
            # 모의투자용 TR ID (신버전)
            if order_type == "buy":
                tr_id = "VTTC0012U"  # 모의투자 매수 (신버전)
            else:  # sell
                tr_id = "VTTC0011U"  # 모의투자 매도 (신버전)
        
        # API 엔드포인트
        endpoint = "/uapi/domestic-stock/v1/trading/order-cash"
        
        # 요청 파라미터 구성 (대문자 키 사용)
        params = {
            "CANO": self.auth.account,           # 종합계좌번호
            "ACNT_PRDT_CD": self.auth.product,   # 계좌상품코드
            "PDNO": stock_code,                  # 상품번호(종목코드)
            "ORD_DVSN": order_division,          # 주문구분
            "ORD_QTY": str(quantity),            # 주문수량
            "ORD_UNPR": price,                   # 주문단가
            "EXCG_ID_DVSN_CD": excg_id_dvsn_cd,  # 거래소ID구분코드
        }
        
        # 매도 시 매도유형 추가 (매도 주문일 때만)
        if order_type == "sell":
            params["SLL_TYPE"] = "01"  # 기본값: 보통 매도
        
        # 디버깅을 위한 주문 정보 로깅
        logger.info(f"주문 파라미터: {params}")
        logger.info(f"TR_ID: {tr_id}, 환경: {self.auth.env}")
        
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
                    'message': response.get('msg1', '주문이 정상적으로 처리되었습니다.'),
                    'data': response
                }
                return result
            else:
                # 실패
                result = {
                    'success': False,
                    'order_no': '',
                    'message': f"[{response.get('msg_cd', '')}] {response.get('msg1', '주문 실패')}",
                    'data': response
                }
                return result
                
        except Exception as e:
            # 예외 발생
            result = {
                'success': False,
                'order_no': '',
                'message': f"주문 중 오류 발생: {str(e)}",
                'data': {}
            }
            return result
    
    def buy_market_order(self, stock_code: str, quantity: int) -> Dict[str, Any]:
        """시장가 매수 주문을 실행합니다.
        
        Args:
            stock_code (str): 종목코드 (예: "005930")
            quantity (int): 주문수량
            
        Returns:
            dict: 주문 결과
        """
        return self.order_cash(
            stock_code=stock_code,
            order_type="buy",
            quantity=quantity,
            price="0",
            order_division="01"
        )
    
    def sell_market_order(self, stock_code: str, quantity: int) -> Dict[str, Any]:
        """시장가 매도 주문을 실행합니다.
        
        Args:
            stock_code (str): 종목코드 (예: "005930")
            quantity (int): 주문수량
            
        Returns:
            dict: 주문 결과
        """
        return self.order_cash(
            stock_code=stock_code,
            order_type="sell",
            quantity=quantity,
            price="0",
            order_division="01"
        )
    
    def buy_limit_order(self, stock_code: str, quantity: int, price: int) -> Dict[str, Any]:
        """지정가 매수 주문을 실행합니다.
        
        Args:
            stock_code (str): 종목코드 (예: "005930")
            quantity (int): 주문수량
            price (int): 주문단가
            
        Returns:
            dict: 주문 결과
        """
        return self.order_cash(
            stock_code=stock_code,
            order_type="buy",
            quantity=quantity,
            price=str(price),
            order_division="00"
        )
    
    def sell_limit_order(self, stock_code: str, quantity: int, price: int) -> Dict[str, Any]:
        """지정가 매도 주문을 실행합니다.
        
        Args:
            stock_code (str): 종목코드 (예: "005930")
            quantity (int): 주문수량
            price (int): 주문단가
            
        Returns:
            dict: 주문 결과
        """
        return self.order_cash(
            stock_code=stock_code,
            order_type="sell",
            quantity=quantity,
            price=str(price),
            order_division="00"
        )
