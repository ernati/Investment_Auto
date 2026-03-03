# -*- coding: utf-8 -*-
"""
KIS Trading Module
한국투자증권 Open Trading API 거래(매수/매도) 모듈
"""

import logging
import pandas as pd
import time
from datetime import datetime
from typing import Optional, Dict, Any

from .kis_api_utils import execute_api_request_with_retry, build_api_headers
from .demo_cash_manager import get_demo_cash_manager


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
                
                # 모의투자 환경에서만 주문 성공 시 가상 현금 잔액 업데이트
                if self.auth.env == "demo":
                    try:
                        demo_manager = get_demo_cash_manager(self.auth.account)
                        
                        # 체결가격 확인 (재시도 로직 포함)
                        executed_price = self._get_execution_price_with_retry(
                            output, stock_code, price, order_division, result['order_no']
                        )
                        
                        if executed_price is None:
                            # 마지막 방법: 시장가 반영 (모의투자에서만)
                            logger.warning(f"Demo 체결가 재시도 모두 실패 - 시장가 반영: {stock_code}")
                            executed_price = self._get_current_market_price(stock_code)
                            
                            if executed_price is None:
                                # 최종 실패 - 현금 업데이트 보류
                                logger.warning(f"Demo 시장가도 조회 실패 - 현금 업데이트 보류: {stock_code}")
                                logger.info("체결 확인 후 수동으로 현금 업데이트를 진행하세요.")
                            else:
                                logger.info(f"Demo 시장가 반영: {executed_price:,}원")
                        
                        if executed_price is not None:
                            executed_quantity = quantity  # 일반적으로 주문수량과 동일
                            
                            if order_type == "buy":
                                # 매수: 현금 차감
                                cash_updated = demo_manager.buy_stock(stock_code, executed_quantity, executed_price)
                                if cash_updated:
                                    logger.info(f"Demo 매수 현금 차감: {stock_code} {executed_quantity}주 x {executed_price:,}원 = {executed_quantity * executed_price:,}원")
                                else:
                                    logger.warning(f"Demo 매수 현금 차감 실패: 잔액 부족")
                            else:  # sell
                                # 매도: 현금 증가
                                cash_updated = demo_manager.sell_stock(stock_code, executed_quantity, executed_price) 
                                if cash_updated:
                                    logger.info(f"Demo 매도 현금 증가: {stock_code} {executed_quantity}주 x {executed_price:,}원 = {executed_quantity * executed_price:,}원")
                                else:
                                    logger.warning(f"Demo 매도 현금 증가 실패")
                    
                    except Exception as e:
                        logger.warning(f"Demo 현금 업데이트 실패: {e}")
                
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
    
    def _get_execution_price_with_retry(self, api_output: Dict[str, Any], stock_code: str, 
                                       price: str, order_division: str, order_no: str) -> Optional[float]:
        """
        체결가격 확인 (재시도 로직 포함).
        모의투자 전용 버전으로, 3번 재시도 후 체결가 미확인 시 시장가 반영 가능.
        
        Args:
            api_output (dict): KIS API 주문 응답의 output 부분
            stock_code (str): 종목코드
            price (str): 주문단가
            order_division (str): 주문구분
            order_no (str): 주문번호
            
        Returns:
            float or None: 체결 가격 또는 None (확인 불가 시)
        """
        # 중요: 모의투자 환경에서만 동작하도록 보장
        if self.auth.env != "demo":
            logger.error("중요: 체결가 재시도는 모의투자에서만 동작합니다!")
            return None
        
        try:
            # 1. 지정가 주문인 경우 입력된 가격 사용
            if price != "0" and order_division == "00":
                executed_price = float(price)
                logger.info(f"지정가 주문 체결가: {executed_price:,}원")
                return executed_price
            
            # 2. 즉시 API 응답에서 체결가 추출 시도
            executed_price = self._extract_executed_price_from_response(api_output)
            if executed_price is not None:
                logger.info(f"API 응답에서 체결가 확인: {executed_price:,}원")
                return executed_price
            
            # 3. 체결정보 재시도 조회 (3번)
            if order_no:
                logger.info(f"Demo 체결정보 재시도 시작: {order_no}")
                retry_price = self._retry_execution_price_inquiry(order_no, stock_code)
                if retry_price is not None:
                    logger.info(f"체결정보 재시도 성공: {retry_price:,}원")
                    return retry_price
            
            # 4. 현재가 API로 실시간 가격 조회 시도
            current_price = self._get_current_market_price(stock_code)
            if current_price is not None:
                logger.info(f"현재가 API로 체결가 확인: {current_price:,}원")
                return current_price
            
            # 5. 모든 방법 실패
            logger.warning(f"모든 체결가 확인 방법 실패: {stock_code}")
            return None
            
        except Exception as e:
            logger.warning(f"체결가 확인 중 오류: {e}")
            return None
    
    def _retry_execution_price_inquiry(self, order_no: str, stock_code: str) -> Optional[float]:
        """
        주문번호로 체결정보를 재시도 조회합니다.
        모의투자 전용 기능입니다.
        
        Args:
            order_no (str): 주문번호
            stock_code (str): 종목코드
            
        Returns:
            float or None: 체결가격 또는 None (실패 시)
        """
        # 중요: 모의투자에서만 동작하도록 보장
        if self.auth.env != "demo":
            logger.error("중요: 체결정보 재시도는 모의투자에서만 동작합니다!")
            return None
        
        if not order_no:
            logger.warning("주문번호가 없어 체결정보 재시도 불가")
            return None
        
        # 3번 재시도 (각 1.5초 간격)
        for attempt in range(3):
            try:
                logger.info(f"체결정보 재시도 {attempt + 1}/3: {order_no}")
                
                # 오늘 날짜 사용
                today = datetime.now().strftime('%Y%m%d')
                
                # inquire_daily_ccld API 호출
                endpoint = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
                
                # TR ID 설정 (demo 환경)
                tr_id = "VTTC8001R"  # 모의투자 주식일별주문체결조회
                
                # 요청 파라미터
                params = {
                    "CANO": self.auth.account[:8],  # 종합계좌번호 (8자리)
                    "ACNT_PRDT_CD": self.auth.product,  # 계좌상품코드
                    "INQR_STRT_DT": today,  # 조회시작일자
                    "INQR_END_DT": today,   # 조회종료일자
                    "SLL_BUY_DVSN_CD": "00",  # 매도매수구분코드 (00:전체)
                    "INQR_DVSN": "00",  # 조회구분 (00:역순, 01:정순)
                    "PDNO": stock_code,  # 상품번호 (종목코드)
                    "CCLD_DVSN": "01",  # 체결구분 (01:체결만)
                    "INQR_DVSN_3": "01",  # 조회구분3 (01:현금)
                    "ORD_GNO_BRNO": "",  # 주문채번지점번호
                    "ODNO": order_no,  # 주문번호
                    "INQR_DVSN_1": "",  # 조회구분1
                    "FK100": "",  # 연속조회검색조건100
                    "NK100": "",  # 연속조회키100
                    "EXCG_ID_DVSN_CD": "KRX"  # 거래소ID구분코드
                }
                
                # API 호출
                response = self._call_api(endpoint, tr_id, params, method='GET')
                
                if response['rt_cd'] == '0':
                    # 성공 시 output1에서 체결정보 추출
                    output1_list = response.get('output1', [])
                    
                    for order_data in output1_list:
                        # 주문번호 치합 확인
                        if order_data.get('odno', '') == order_no:
                            # 체결가격 추출 시도
                            price_fields = [
                                'avg_prvs',       # 평균가 (체결가격)
                                'tot_ccld_amt',   # 총체결금액  
                                'ord_unpr'        # 주문단가
                            ]
                            
                            for field in price_fields:
                                if field in order_data and order_data[field]:
                                    try:
                                        price_value = float(order_data[field])
                                        if price_value > 0:
                                            logger.info(f"체결정보 재조회 성공: {field} = {price_value:,}원")
                                            return price_value
                                    except (ValueError, TypeError):
                                        continue
                            
                            # 체결가격이 없으면 로그 출력 후 다음 시도
                            logger.warning(f"체결정보에서 가격 미발견: {order_no} - 시도 {attempt + 1}")
                            break
                    else:
                        logger.warning(f"주문번호와 일치하는 체결정보 없음: {order_no} - 시도 {attempt + 1}")
                
                else:
                    logger.warning(f"체결정보 조회 API 실패: {response.get('msg1', '')} - 시도 {attempt + 1}")
                
            except Exception as e:
                logger.warning(f"체결정보 재시도 {attempt + 1} 실패: {e}")
            
            # 마지막 시도가 아니면 대기
            if attempt < 2:  # 0, 1번째에만 대기
                time.sleep(1.5)  # 1.5초 대기
        
        logger.warning(f"체결정보 3번 재시도 모두 실패: {order_no}")
        return None
    
    def _get_current_market_price(self, stock_code: str) -> Optional[float]:
        """
        현재 시장가격을 조회합니다.
        
        Args:
            stock_code (str): 종목코드
            
        Returns:
            float or None: 현재가 또는 None (얻어올 수 없어 실패 시)
        """
        try:
            logger.info(f"현재가 조회 시도: {stock_code}")
            
            # 현재가 조회 API 엔드포인트
            endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
            
            # TR ID (모의/실전 구분)
            tr_id = "FHKST01010100" if self.auth.env == "real" else "FHKST01010300"
            
            # 요청 파라미터
            params = {
                "FID_COND_MRKT_DIV_CODE": "J",  # 시장 구분 코드 (J: 주식)
                "FID_INPUT_ISCD": stock_code  # 종목코드
            }
            
            # API 호출
            response = self._call_api(endpoint, tr_id, params, method='GET')
            
            if response['rt_cd'] == '0':
                # 성공 시 output에서 현재가 추출
                output = response.get('output', {})
                current_price_str = output.get('stck_prpr', '')  # 주식현재가
                
                if current_price_str and current_price_str.isdigit():
                    current_price = float(current_price_str)
                    logger.info(f"현재가 조회 성공: {stock_code} = {current_price:,}원")
                    return current_price
                else:
                    logger.warning(f"현재가 데이터 비정상: {current_price_str}")
                    return None
            else:
                logger.warning(f"현재가 조회 API 실패: {response.get('msg1', '')}")
                return None
                
        except Exception as e:
            logger.warning(f"현재가 조회 중 오류: {e}")
            return None
    
    def _extract_executed_price_from_response(self, api_output: Dict[str, Any]) -> Optional[float]:
        """
        API 응답에서 실제 체결가격을 추출합니다.
        
        Args:
            api_output (dict): KIS API 응답의 output 부분
            
        Returns:
            float or None: 체결 가격 또는 None (미발견 시)
        """
        try:
            # KIS API 주문 응답에서 체결 관련 필드 확인
            price_fields = [
                'avg_prvs',      # 평균단가
                'tot_ccld_amt',  # 총체결금액
                'ccld_unpr',     # 체결단가
                'avg_unpr',      # 평균단가
                'ord_unpr'       # 주문단가
            ]
            
            for field in price_fields:
                if field in api_output and api_output[field]:
                    try:
                        price_value = float(api_output[field])
                        if price_value > 0:
                            logger.debug(f"API 응답에서 체결가격 추출: {field} = {price_value:,}원")
                            return price_value
                    except (ValueError, TypeError):
                        continue
            
            return None
            
        except Exception as e:
            logger.debug(f"API 응답 체결가 추출 실패: {e}")
            return None
    
    def _get_current_market_price(self, stock_code: str) -> Optional[float]:
        """
        현재가 API를 통해 실시간 가격을 조회합니다.
        
        Args:
            stock_code (str): 종목코드
            
        Returns:
            float or None: 현재가 또는 None (조회 실패 시)
        """
        try:
            # kis_api_client를 사용하여 현재가 조회
            from .kis_api_client import KISAPIClient
            
            api_client = KISAPIClient(self.auth)
            market_info = api_client.get_market_price(stock_code)
            
            if market_info and '현재가' in market_info:
                try:
                    current_price = float(market_info['현재가'].replace(',', ''))
                    if current_price > 0:
                        logger.debug(f"현재가 API 성공: {stock_code} = {current_price:,}원")
                        return current_price
                except (ValueError, TypeError, AttributeError):
                    pass
            
            return None
            
        except Exception as e:
            logger.debug(f"현재가 API 조회 실패: {e}")
            return None
    
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
