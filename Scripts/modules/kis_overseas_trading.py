# -*- coding: utf-8 -*-
"""
KIS Overseas Trading Module
한국투자증권 Open Trading API 해외주식 거래 모듈

지원 거래소:
- 미국: NASD(나스닥), NYSE(뉴욕), AMEX(아멕스)
- 홍콩: SEHK
- 중국: SHAA(상해), SZAA(심천)
- 일본: TKSE
- 베트남: HASE(하노이), VNSE(호치민)
"""

import logging
from typing import Optional, Dict, Any, Tuple
import pandas as pd

from .kis_api_utils import execute_api_request_with_retry, build_api_headers
from .demo_cash_manager import get_demo_overseas_cash_manager


logger = logging.getLogger(__name__)


# 해외 거래소 코드 매핑
EXCHANGE_CODES = {
    # 미국
    "NASD": {"name": "나스닥", "currency": "USD", "country": "US"},
    "NYSE": {"name": "뉴욕", "currency": "USD", "country": "US"},
    "AMEX": {"name": "아멕스", "currency": "USD", "country": "US"},
    "NAS": {"name": "나스닥(실전)", "currency": "USD", "country": "US"},
    # 홍콩
    "SEHK": {"name": "홍콩", "currency": "HKD", "country": "HK"},
    # 중국
    "SHAA": {"name": "중국상해", "currency": "CNY", "country": "CN"},
    "SZAA": {"name": "중국심천", "currency": "CNY", "country": "CN"},
    # 일본
    "TKSE": {"name": "일본", "currency": "JPY", "country": "JP"},
    # 베트남
    "HASE": {"name": "베트남 하노이", "currency": "VND", "country": "VN"},
    "VNSE": {"name": "베트남 호치민", "currency": "VND", "country": "VN"},
}

# 현재가 조회용 거래소 코드 매핑 (EXCD)
PRICE_EXCHANGE_CODES = {
    "NASD": "NAS",
    "NYSE": "NYS",
    "AMEX": "AMS",
    "NAS": "NAS",
    "NYS": "NYS",
    "AMS": "AMS",
    "SEHK": "HKS",
    "SHAA": "SHS",
    "SZAA": "SZS",
    "TKSE": "TSE",
    "HASE": "HNX",
    "VNSE": "HSX",
}


class KISOverseasTrading:
    """한국투자증권 API 해외주식 거래 클래스"""
    
    def __init__(self, auth):
        """
        Args:
            auth: KISAuth 인증 객체
        """
        self.auth = auth
        
    def _call_api(self, endpoint: str, tr_id: str, params: Dict = None, 
                  method: str = 'POST') -> Dict[str, Any]:
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
                context=f"KIS Overseas Trading API ({tr_id})",
                kis_auth=self.auth
            )
            return response_data
        except Exception as e:
            raise Exception(f"API 호출 실패: {str(e)}")
    
    def _get_order_tr_id(self, exchange_code: str, order_type: str) -> str:
        """거래소 코드와 주문 유형에 따른 TR ID를 반환합니다.
        
        Args:
            exchange_code (str): 해외거래소코드
            order_type (str): 주문유형 ("buy" 또는 "sell")
            
        Returns:
            str: TR ID (실전투자용, 모의투자는 자동 변환됨)
        """
        if order_type == "buy":
            if exchange_code in ("NASD", "NYSE", "AMEX", "NAS"):
                return "TTTT1002U"  # 미국 매수 [모의: VTTT1002U]
            elif exchange_code == "SEHK":
                return "TTTS1002U"  # 홍콩 매수 [모의: VTTS1002U]
            elif exchange_code == "SHAA":
                return "TTTS0202U"  # 중국상해 매수 [모의: VTTS0202U]
            elif exchange_code == "SZAA":
                return "TTTS0305U"  # 중국심천 매수 [모의: VTTS0305U]
            elif exchange_code == "TKSE":
                return "TTTS0308U"  # 일본 매수 [모의: VTTS0308U]
            elif exchange_code in ("HASE", "VNSE"):
                return "TTTS0311U"  # 베트남 매수 [모의: VTTS0311U]
        else:  # sell
            if exchange_code in ("NASD", "NYSE", "AMEX", "NAS"):
                return "TTTT1006U"  # 미국 매도 [모의: VTTT1006U]
            elif exchange_code == "SEHK":
                return "TTTS1001U"  # 홍콩 매도 [모의: VTTS1001U]
            elif exchange_code == "SHAA":
                return "TTTS1005U"  # 중국상해 매도 [모의: VTTS1005U]
            elif exchange_code == "SZAA":
                return "TTTS0304U"  # 중국심천 매도 [모의: VTTS0304U]
            elif exchange_code == "TKSE":
                return "TTTS0307U"  # 일본 매도 [모의: VTTS0307U]
            elif exchange_code in ("HASE", "VNSE"):
                return "TTTS0310U"  # 베트남 매도 [모의: VTTS0310U]
        
        raise ValueError(f"지원하지 않는 거래소 코드: {exchange_code}")
    
    def order(
        self,
        stock_code: str,
        exchange_code: str,
        order_type: str,
        quantity: int,
        price: str = "0",
        order_division: str = "00"
    ) -> Dict[str, Any]:
        """해외주식 주문을 실행합니다.
        
        Args:
            stock_code (str): 종목코드 (예: "AAPL", "TSLA")
            exchange_code (str): 해외거래소코드
                - "NASD": 나스닥
                - "NYSE": 뉴욕
                - "AMEX": 아멕스
                - "SEHK": 홍콩
                - "SHAA": 중국상해
                - "SZAA": 중국심천
                - "TKSE": 일본
                - "HASE": 베트남 하노이
                - "VNSE": 베트남 호치민
            order_type (str): 주문유형 ("buy": 매수, "sell": 매도)
            quantity (int): 주문수량
            price (str): 주문단가 (기본값: "0")
                - 시장가 주문 시에도 "0" 입력
            order_division (str): 주문구분 (기본값: "00")
                [미국 매수주문 - TTTT1002U]
                - "00": 지정가
                - "32": LOO(장개시지정가)
                - "34": LOC(장마감지정가)
                * 모의투자는 "00" 지정가만 가능
                
                [미국 매도주문 - TTTT1006U]
                - "00": 지정가
                - "31": MOO(장개시시장가)
                - "32": LOO(장개시지정가)
                - "33": MOC(장마감시장가)
                - "34": LOC(장마감지정가)
                * 모의투자는 "00" 지정가만 가능
                
                [홍콩 매도주문 - TTTS1001U]
                - "00": 지정가
                - "50": 단주지정가
                
                [그 외]
                - 제한 없음
            
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
        
        if exchange_code.upper() not in EXCHANGE_CODES:
            raise ValueError(f"지원하지 않는 거래소 코드: {exchange_code}")
        
        exchange_code = exchange_code.upper()
        
        # TR_ID 설정 (환경에 따라 자동 변환됨 - build_api_headers에서 처리)
        tr_id = self._get_order_tr_id(exchange_code, order_type)
        
        # API 엔드포인트
        endpoint = "/uapi/overseas-stock/v1/trading/order"
        
        # 요청 파라미터 구성
        params = {
            "CANO": self.auth.account,           # 종합계좌번호
            "ACNT_PRDT_CD": self.auth.product,   # 계좌상품코드
            "OVRS_EXCG_CD": exchange_code,       # 해외거래소코드
            "PDNO": stock_code.upper(),          # 종목코드
            "ORD_QTY": str(quantity),            # 주문수량
            "OVRS_ORD_UNPR": price,              # 해외주문단가
            "CTAC_TLNO": "",                     # 연락전화번호
            "MGCO_APTM_ODNO": "",                # 운용사지정주문번호
            "ORD_SVR_DVSN_CD": "0",              # 주문서버구분코드
            "ORD_DVSN": order_division,          # 주문구분
        }
        
        # 매도 시 매도유형 추가
        if order_type == "sell":
            params["SLL_TYPE"] = "00"  # 기본값: 보통 매도
        else:
            params["SLL_TYPE"] = ""
        
        # 디버깅을 위한 주문 정보 로깅
        logger.info(f"해외주식 주문 파라미터: {params}")
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
                    'data': response,
                    # 추가 필드
                    'symbol': stock_code.upper(),
                    'exchange': exchange_code,
                    'side': order_type,
                    'quantity': quantity,
                    'price': float(price) if price != "0" else 0
                }
                
                # 모의투자 환경에서 주문 성공 시 가상 외화 잔고 업데이트
                if self.auth.env == "demo":
                    try:
                        demo_manager = get_demo_overseas_cash_manager(self.auth.account)
                        executed_price = float(price) if price != "0" else 0
                        
                        # 체결가격이 0인 경우 현재가 조회
                        if executed_price == 0:
                            price_info = self.get_current_price(stock_code, exchange_code)
                            if price_info.get('success') and price_info.get('current_price', 0) > 0:
                                executed_price = price_info['current_price']
                                result['price'] = executed_price
                        
                        if executed_price > 0:
                            if order_type == "buy":
                                cash_result = demo_manager.buy_stock(
                                    stock_code=stock_code,
                                    exchange_code=exchange_code,
                                    quantity=quantity,
                                    price=executed_price
                                )
                                if cash_result.get('success'):
                                    logger.info(f"Demo 해외 매수 현금 차감 완료: {cash_result}")
                                else:
                                    logger.warning(f"Demo 해외 매수 현금 차감 실패: {cash_result.get('error')}")
                            else:  # sell
                                cash_result = demo_manager.sell_stock(
                                    stock_code=stock_code,
                                    exchange_code=exchange_code,
                                    quantity=quantity,
                                    price=executed_price
                                )
                                if cash_result.get('success'):
                                    logger.info(f"Demo 해외 매도 현금 증가 완료: {cash_result}")
                                else:
                                    logger.warning(f"Demo 해외 매도 현금 증가 실패: {cash_result.get('error')}")
                        else:
                            logger.warning(f"Demo 체결가격 확인 불가 - 현금 업데이트 보류")
                    except Exception as e:
                        logger.warning(f"Demo 해외 현금 업데이트 실패: {e}")
                
                logger.info(f"해외주식 주문 성공: {stock_code} {order_type} {quantity}주 @ {price}")
                return result
            else:
                # 실패
                result = {
                    'success': False,
                    'order_no': '',
                    'message': f"[{response.get('msg_cd', '')}] {response.get('msg1', '주문 실패')}",
                    'data': response
                }
                logger.error(f"해외주식 주문 실패: {result['message']}")
                return result
                
        except Exception as e:
            # 예외 발생
            result = {
                'success': False,
                'order_no': '',
                'message': f"주문 중 오류 발생: {str(e)}",
                'data': {}
            }
            logger.error(f"해외주식 주문 예외: {str(e)}")
            return result
    
    def daytime_order(
        self,
        stock_code: str,
        exchange_code: str,
        order_type: str,
        quantity: int,
        price: str,
        order_division: str = "00"
    ) -> Dict[str, Any]:
        """미국 주간 주문을 실행합니다. (주간거래 시간에만 가능)
        
        미국 주간거래 시간: 한국시간 기준 23:30 ~ 06:00 (써머타임 시 22:30 ~ 05:00)
        
        Args:
            stock_code (str): 종목코드 (예: "AAPL", "TSLA")
            exchange_code (str): 해외거래소코드 ("NASD", "NYSE", "AMEX")
            order_type (str): 주문유형 ("buy": 매수, "sell": 매도)
            quantity (int): 주문수량
            price (str): 주문단가 (지정가만 가능)
            order_division (str): 주문구분 (기본값: "00" - 지정가만 가능)
            
        Returns:
            dict: 주문 결과
        """
        # 파라미터 검증
        if order_type not in ["buy", "sell"]:
            raise ValueError("order_type은 'buy' 또는 'sell'이어야 합니다.")
        
        if quantity <= 0:
            raise ValueError("quantity는 0보다 커야 합니다.")
        
        if exchange_code.upper() not in ("NASD", "NYSE", "AMEX"):
            raise ValueError("주간거래는 미국 거래소(NASD, NYSE, AMEX)만 지원합니다.")
        
        exchange_code = exchange_code.upper()
        
        # TR_ID 설정
        if order_type == "buy":
            tr_id = "TTTS6036U"  # 미국 주간 매수
        else:
            tr_id = "TTTS6037U"  # 미국 주간 매도
        
        # API 엔드포인트
        endpoint = "/uapi/overseas-stock/v1/trading/daytime-order"
        
        # 요청 파라미터 구성
        params = {
            "CANO": self.auth.account,           # 종합계좌번호
            "ACNT_PRDT_CD": self.auth.product,   # 계좌상품코드
            "OVRS_EXCG_CD": exchange_code,       # 해외거래소코드
            "PDNO": stock_code.upper(),          # 종목코드
            "ORD_QTY": str(quantity),            # 주문수량
            "OVRS_ORD_UNPR": price,              # 해외주문단가
            "CTAC_TLNO": "",                     # 연락전화번호
            "MGCO_APTM_ODNO": "",                # 운용사지정주문번호
            "ORD_SVR_DVSN_CD": "0",              # 주문서버구분코드
            "ORD_DVSN": order_division,          # 주문구분 (지정가만)
        }
        
        logger.info(f"미국 주간주문 파라미터: {params}")
        logger.info(f"TR_ID: {tr_id}, 환경: {self.auth.env}")
        
        try:
            response = self._call_api(endpoint, tr_id, params, method='POST')
            
            if response['rt_cd'] == '0':
                output = response.get('output', {})
                result = {
                    'success': True,
                    'order_no': output.get('ODNO', ''),
                    'order_time': output.get('ORD_TMD', ''),
                    'message': response.get('msg1', '주간주문이 정상적으로 처리되었습니다.'),
                    'data': response,
                    'symbol': stock_code.upper(),
                    'exchange': exchange_code,
                    'side': order_type,
                    'quantity': quantity,
                    'price': float(price)
                }
                logger.info(f"미국 주간주문 성공: {stock_code} {order_type} {quantity}주 @ {price}")
                return result
            else:
                result = {
                    'success': False,
                    'order_no': '',
                    'message': f"[{response.get('msg_cd', '')}] {response.get('msg1', '주문 실패')}",
                    'data': response
                }
                logger.error(f"미국 주간주문 실패: {result['message']}")
                return result
                
        except Exception as e:
            result = {
                'success': False,
                'order_no': '',
                'message': f"주간주문 중 오류 발생: {str(e)}",
                'data': {}
            }
            logger.error(f"미국 주간주문 예외: {str(e)}")
            return result
    
    def modify_cancel_order(
        self,
        stock_code: str,
        exchange_code: str,
        original_order_no: str,
        action: str,
        quantity: int = 0,
        price: str = "0"
    ) -> Dict[str, Any]:
        """해외주식 주문을 정정하거나 취소합니다.
        
        Args:
            stock_code (str): 종목코드
            exchange_code (str): 해외거래소코드
            original_order_no (str): 원주문번호
            action (str): 처리구분 ("modify": 정정, "cancel": 취소)
            quantity (int): 정정 수량 (정정 시 필수)
            price (str): 정정 단가 (정정 시 필수, 취소 시 "0")
            
        Returns:
            dict: 처리 결과
        """
        if action not in ["modify", "cancel"]:
            raise ValueError("action은 'modify' 또는 'cancel'이어야 합니다.")
        
        exchange_code = exchange_code.upper()
        
        # 정정취소구분코드
        rvse_cncl_dvsn_cd = "01" if action == "modify" else "02"
        
        # TR_ID 설정
        tr_id = "TTTT1004U"  # 해외주식 정정취소 [모의: VTTT1004U]
        
        # API 엔드포인트
        endpoint = "/uapi/overseas-stock/v1/trading/order-rvsecncl"
        
        # 요청 파라미터 구성
        params = {
            "CANO": self.auth.account,
            "ACNT_PRDT_CD": self.auth.product,
            "OVRS_EXCG_CD": exchange_code,
            "PDNO": stock_code.upper(),
            "ORGN_ODNO": original_order_no,      # 원주문번호
            "RVSE_CNCL_DVSN_CD": rvse_cncl_dvsn_cd,  # 정정취소구분
            "ORD_QTY": str(quantity) if action == "modify" else "0",
            "OVRS_ORD_UNPR": price if action == "modify" else "0",
            "MGCO_APTM_ODNO": "",
            "ORD_SVR_DVSN_CD": "0",
        }
        
        action_name = "정정" if action == "modify" else "취소"
        logger.info(f"해외주식 주문 {action_name} 파라미터: {params}")
        
        try:
            response = self._call_api(endpoint, tr_id, params, method='POST')
            
            if response['rt_cd'] == '0':
                output = response.get('output', {})
                result = {
                    'success': True,
                    'order_no': output.get('ODNO', ''),
                    'message': response.get('msg1', f'주문 {action_name}이 정상적으로 처리되었습니다.'),
                    'data': response,
                    'original_order_no': original_order_no,
                    'action': action
                }
                logger.info(f"해외주식 주문 {action_name} 성공: {original_order_no}")
                return result
            else:
                result = {
                    'success': False,
                    'order_no': '',
                    'message': f"[{response.get('msg_cd', '')}] {response.get('msg1', f'주문 {action_name} 실패')}",
                    'data': response
                }
                logger.error(f"해외주식 주문 {action_name} 실패: {result['message']}")
                return result
                
        except Exception as e:
            result = {
                'success': False,
                'order_no': '',
                'message': f"주문 {action_name} 중 오류 발생: {str(e)}",
                'data': {}
            }
            logger.error(f"해외주식 주문 {action_name} 예외: {str(e)}")
            return result
    
    def get_current_price(
        self,
        stock_code: str,
        exchange_code: str
    ) -> Dict[str, Any]:
        """해외주식 현재체결가를 조회합니다.
        
        Args:
            stock_code (str): 종목코드 (예: "AAPL")
            exchange_code (str): 해외거래소코드 (예: "NASD", "NYSE")
            
        Returns:
            dict: 현재가 정보
                - success (bool): 성공 여부
                - current_price (float): 현재가
                - change (float): 전일대비
                - change_rate (float): 전일대비율
                - data (dict): 원본 응답 데이터
        """
        exchange_code = exchange_code.upper()
        
        # 현재가 조회용 거래소 코드 변환
        excd = PRICE_EXCHANGE_CODES.get(exchange_code, exchange_code[:3])
        
        # TR_ID 설정 (실전/모의 공통)
        tr_id = "HHDFS00000300"
        
        # API 엔드포인트
        endpoint = "/uapi/overseas-price/v1/quotations/price"
        
        # 요청 파라미터 구성
        params = {
            "AUTH": "",
            "EXCD": excd,
            "SYMB": stock_code.upper(),
        }
        
        try:
            response = self._call_api(endpoint, tr_id, params, method='GET')
            
            if response['rt_cd'] == '0':
                output = response.get('output', {})
                
                # 현재가 추출
                current_price_str = output.get('last', output.get('stck_prpr', '0'))
                change_str = output.get('diff', output.get('prdy_vrss', '0'))
                change_rate_str = output.get('rate', output.get('prdy_ctrt', '0'))
                
                try:
                    current_price = float(current_price_str) if current_price_str else 0
                    change = float(change_str) if change_str else 0
                    change_rate = float(change_rate_str) if change_rate_str else 0
                except (ValueError, TypeError):
                    current_price = 0
                    change = 0
                    change_rate = 0
                
                result = {
                    'success': True,
                    'symbol': stock_code.upper(),
                    'exchange': exchange_code,
                    'current_price': current_price,
                    'change': change,
                    'change_rate': change_rate,
                    'message': '현재가 조회 성공',
                    'data': output
                }
                logger.info(f"해외주식 현재가 조회 성공: {stock_code} = {current_price}")
                return result
            else:
                result = {
                    'success': False,
                    'current_price': 0,
                    'message': f"[{response.get('msg_cd', '')}] {response.get('msg1', '현재가 조회 실패')}",
                    'data': response
                }
                logger.error(f"해외주식 현재가 조회 실패: {result['message']}")
                return result
                
        except Exception as e:
            result = {
                'success': False,
                'current_price': 0,
                'message': f"현재가 조회 중 오류 발생: {str(e)}",
                'data': {}
            }
            logger.error(f"해외주식 현재가 조회 예외: {str(e)}")
            return result
    
    def get_balance(
        self,
        exchange_code: str = "NASD",
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """해외주식 잔고를 조회합니다.
        
        Args:
            exchange_code (str): 해외거래소코드 (기본값: "NASD")
                - 모의투자: NASD, NYSE, AMEX, SEHK, SHAA, SZAA, TKSE, HASE, VNSE
                - 실전투자: NASD(미국전체), NAS, NYSE, AMEX 등
            currency (str): 거래통화코드 (기본값: "USD")
                - "USD": 미국달러
                - "HKD": 홍콩달러
                - "CNY": 중국위안화
                - "JPY": 일본엔화
                - "VND": 베트남동
            
        Returns:
            dict: 잔고 정보
                - success (bool): 성공 여부
                - holdings (list): 보유 종목 리스트
                - summary (dict): 요약 정보
                - data (dict): 원본 응답 데이터
        """
        exchange_code = exchange_code.upper()
        currency = currency.upper()
        
        # TR_ID 설정
        tr_id = "TTTS3012R"  # 해외주식 잔고 [모의: VTTS3012R]
        
        # API 엔드포인트
        endpoint = "/uapi/overseas-stock/v1/trading/inquire-balance"
        
        # 요청 파라미터 구성
        params = {
            "CANO": self.auth.account,
            "ACNT_PRDT_CD": self.auth.product,
            "OVRS_EXCG_CD": exchange_code,
            "TR_CRCY_CD": currency,
            "CTX_AREA_FK200": "",
            "CTX_AREA_NK200": "",
        }
        
        try:
            response = self._call_api(endpoint, tr_id, params, method='GET')
            
            if response['rt_cd'] == '0':
                output1 = response.get('output1', [])  # 보유 종목
                output2 = response.get('output2', {})  # 요약 정보
                
                # output1이 리스트가 아닌 경우 처리
                if not isinstance(output1, list):
                    output1 = [output1] if output1 else []
                
                # 보유 종목 정리
                holdings = []
                for item in output1:
                    if item:
                        holding = {
                            'symbol': item.get('ovrs_pdno', ''),       # 해외상품번호
                            'name': item.get('ovrs_item_name', ''),    # 해외종목명
                            'quantity': int(item.get('ovrs_cblc_qty', 0)),  # 해외잔고수량
                            'avg_price': float(item.get('pchs_avg_pric', 0)),  # 매입평균가격
                            'current_price': float(item.get('ovrs_stck_evlu_amt', 0)),  # 해외주식평가금액
                            'profit_loss': float(item.get('frcr_evlu_pfls_amt', 0)),  # 외화평가손익금액
                            'profit_rate': float(item.get('evlu_pfls_rt', 0)),  # 평가손익율
                            'exchange': item.get('ovrs_excg_cd', ''),  # 해외거래소코드
                        }
                        if holding['quantity'] > 0:
                            holdings.append(holding)
                
                # 요약 정보 정리
                if isinstance(output2, list) and output2:
                    output2 = output2[0]
                
                summary = {}
                if output2:
                    summary = {
                        'total_evaluation': float(output2.get('tot_evlu_pfls_amt', 0)),  # 총평가손익금액
                        'total_profit_rate': float(output2.get('tot_pftrt', 0)),  # 총수익율
                        'total_purchase': float(output2.get('pchs_amt_smtl_amt', 0)),  # 매입금액합계
                        'total_evaluation_amount': float(output2.get('evlu_amt_smtl_amt', 0)),  # 평가금액합계
                    }
                
                result = {
                    'success': True,
                    'holdings': holdings,
                    'summary': summary,
                    'message': '잔고 조회 성공',
                    'data': response
                }
                logger.info(f"해외주식 잔고 조회 성공: {len(holdings)}개 종목")
                return result
            else:
                result = {
                    'success': False,
                    'holdings': [],
                    'summary': {},
                    'message': f"[{response.get('msg_cd', '')}] {response.get('msg1', '잔고 조회 실패')}",
                    'data': response
                }
                logger.error(f"해외주식 잔고 조회 실패: {result['message']}")
                return result
                
        except Exception as e:
            result = {
                'success': False,
                'holdings': [],
                'summary': {},
                'message': f"잔고 조회 중 오류 발생: {str(e)}",
                'data': {}
            }
            logger.error(f"해외주식 잔고 조회 예외: {str(e)}")
            return result
    
    # 편의 메서드들
    def buy_limit_order(
        self,
        stock_code: str,
        exchange_code: str,
        quantity: int,
        price: float
    ) -> Dict[str, Any]:
        """지정가 매수 주문을 실행합니다.
        
        Args:
            stock_code (str): 종목코드
            exchange_code (str): 해외거래소코드
            quantity (int): 주문수량
            price (float): 주문단가
            
        Returns:
            dict: 주문 결과
        """
        return self.order(
            stock_code=stock_code,
            exchange_code=exchange_code,
            order_type="buy",
            quantity=quantity,
            price=str(price),
            order_division="00"
        )
    
    def sell_limit_order(
        self,
        stock_code: str,
        exchange_code: str,
        quantity: int,
        price: float
    ) -> Dict[str, Any]:
        """지정가 매도 주문을 실행합니다.
        
        Args:
            stock_code (str): 종목코드
            exchange_code (str): 해외거래소코드
            quantity (int): 주문수량
            price (float): 주문단가
            
        Returns:
            dict: 주문 결과
        """
        return self.order(
            stock_code=stock_code,
            exchange_code=exchange_code,
            order_type="sell",
            quantity=quantity,
            price=str(price),
            order_division="00"
        )
    
    def buy_market_order_us(
        self,
        stock_code: str,
        exchange_code: str,
        quantity: int
    ) -> Dict[str, Any]:
        """미국 주식 시장가 매수 주문을 실행합니다.
        
        미국 주식은 시장가 주문 시 LOO(장개시지정가) 사용
        
        Args:
            stock_code (str): 종목코드
            exchange_code (str): 해외거래소코드 ("NASD", "NYSE", "AMEX")
            quantity (int): 주문수량
            
        Returns:
            dict: 주문 결과
        """
        # 미국 시장가는 지원하지 않으므로 LOO 사용
        # 모의투자에서는 지정가만 가능하므로 현재가 조회 후 지정가로 주문
        if self.auth.env == "demo":
            price_info = self.get_current_price(stock_code, exchange_code)
            if price_info['success'] and price_info['current_price'] > 0:
                # 현재가보다 약간 높은 가격으로 매수 (체결 확률 높임)
                price = round(price_info['current_price'] * 1.01, 2)
                return self.buy_limit_order(stock_code, exchange_code, quantity, price)
            else:
                return {
                    'success': False,
                    'order_no': '',
                    'message': '현재가 조회 실패로 시장가 매수 불가',
                    'data': {}
                }
        else:
            return self.order(
                stock_code=stock_code,
                exchange_code=exchange_code,
                order_type="buy",
                quantity=quantity,
                price="0",
                order_division="32"  # LOO
            )
    
    def sell_market_order_us(
        self,
        stock_code: str,
        exchange_code: str,
        quantity: int
    ) -> Dict[str, Any]:
        """미국 주식 시장가 매도 주문을 실행합니다.
        
        미국 주식 매도 시 MOO(장개시시장가) 사용
        
        Args:
            stock_code (str): 종목코드
            exchange_code (str): 해외거래소코드 ("NASD", "NYSE", "AMEX")
            quantity (int): 주문수량
            
        Returns:
            dict: 주문 결과
        """
        # 모의투자에서는 지정가만 가능하므로 현재가 조회 후 지정가로 주문
        if self.auth.env == "demo":
            price_info = self.get_current_price(stock_code, exchange_code)
            if price_info['success'] and price_info['current_price'] > 0:
                # 현재가보다 약간 낮은 가격으로 매도 (체결 확률 높임)
                price = round(price_info['current_price'] * 0.99, 2)
                return self.sell_limit_order(stock_code, exchange_code, quantity, price)
            else:
                return {
                    'success': False,
                    'order_no': '',
                    'message': '현재가 조회 실패로 시장가 매도 불가',
                    'data': {}
                }
        else:
            return self.order(
                stock_code=stock_code,
                exchange_code=exchange_code,
                order_type="sell",
                quantity=quantity,
                price="0",
                order_division="31"  # MOO
            )
    
    def cancel_order(
        self,
        stock_code: str,
        exchange_code: str,
        original_order_no: str
    ) -> Dict[str, Any]:
        """주문을 취소합니다.
        
        Args:
            stock_code (str): 종목코드
            exchange_code (str): 해외거래소코드
            original_order_no (str): 취소할 원주문번호
            
        Returns:
            dict: 취소 결과
        """
        return self.modify_cancel_order(
            stock_code=stock_code,
            exchange_code=exchange_code,
            original_order_no=original_order_no,
            action="cancel"
        )
    
    def modify_order(
        self,
        stock_code: str,
        exchange_code: str,
        original_order_no: str,
        quantity: int,
        price: float
    ) -> Dict[str, Any]:
        """주문을 정정합니다.
        
        Args:
            stock_code (str): 종목코드
            exchange_code (str): 해외거래소코드
            original_order_no (str): 정정할 원주문번호
            quantity (int): 정정 수량
            price (float): 정정 단가
            
        Returns:
            dict: 정정 결과
        """
        return self.modify_cancel_order(
            stock_code=stock_code,
            exchange_code=exchange_code,
            original_order_no=original_order_no,
            action="modify",
            quantity=quantity,
            price=str(price)
        )
