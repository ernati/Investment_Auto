# -*- coding: utf-8 -*-
"""
KIS API Utilities Module
한국투자증권 Open API 공통 유틸리티 함수들
- 헤더 생성
- API 응답 검증
- API 요청 실행
- 에러 처리
- Rate limiting 처리
"""

import logging
import time
from typing import Dict, Optional, Any
import requests

from .kis_auth import KISAuth


logger = logging.getLogger(__name__)

# KIS API Rate Limiting 설정
# 실전 환경: 0.1초, 모의 환경: 0.5초 지연
_RATE_LIMIT_DELAY = {
    "demo": 0.5,    # 모의투자 환경
    "real": 0.1     # 실전투자 환경
}


def smart_sleep(env: str = "demo", debug: bool = False) -> None:
    """
    KIS API 호출 사이에 적절한 지연을 추가하여 rate limiting을 방지합니다.
    
    Args:
        env (str): 환경 ("demo" 또는 "real")
        debug (bool): 디버그 로그 출력 여부
    """
    delay = _RATE_LIMIT_DELAY.get(env, 0.5)
    
    if debug:
        logger.debug(f"[RateLimit] Sleeping {delay}s for {env} environment")
    
    time.sleep(delay)


def _normalize_tr_id(tr_id: str, env: str) -> str:
    if env != "demo":
        return tr_id

    if not tr_id:
        return tr_id

    if tr_id[0] in ("T", "J", "C"):
        return "V" + tr_id[1:]

    return tr_id


def build_api_headers(
    kis_auth: KISAuth,
    tr_id: str,
    tr_cont: str = ""
) -> Dict[str, str]:
    """
    KIS API 요청 헤더를 생성합니다.
    
    Args:
        kis_auth (KISAuth): 인증 정보
        tr_id (str): Transaction ID (예: 'TTTC8434R')
        tr_cont (str): Transaction Continue (페이지네이션용, 기본값: "")
    
    Returns:
        Dict[str, str]: API 요청 헤더
    """
    token = kis_auth.authenticate()
    
    tr_id = _normalize_tr_id(tr_id, kis_auth.env)

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {token}",
        "appKey": kis_auth.appkey,
        "appSecret": kis_auth.appsecret,
        "tr_id": tr_id,
        "custtype": "P",  # 개인고객
        "User-Agent": "Python",
    }
    
    if tr_cont:
        headers["tr_cont"] = tr_cont
    
    return headers


def validate_api_response(
    response_data: Dict[str, Any],
    context: str = "KIS API"
) -> tuple[bool, Optional[str]]:
    """
    KIS API 응답을 검증합니다.
    
    KIS API는 성공 시 rt_cd가 '0'이어야 합니다.
    
    Args:
        response_data (Dict[str, Any]): API 응답 데이터
        context (str): 에러 로그에 포함할 컨텍스트 정보
    
    Returns:
        (success, error_message): (성공 여부, 에러 메시지)
            - success가 True이면 error_message는 None
            - success가 False이면 error_message에 에러 내용 포함
    """
    rt_cd = response_data.get('rt_cd', '')
    
    if rt_cd == '0':
        return True, None
    else:
        # 더 자세한 에러 정보 추출
        msg_cd = response_data.get('msg_cd', '')
        msg1 = response_data.get('msg1', '')
        msg = response_data.get('msg', 'Unknown error')
        
        # 에러 메시지 구성
        if msg_cd and msg1:
            error_msg = f"[{msg_cd}] {msg1}"
        elif msg1:
            error_msg = msg1
        else:
            error_msg = msg
            
        # 자세한 로깅
        logger.error(f"{context}: {error_msg} (rt_cd={rt_cd})")
        if msg_cd:
            logger.error(f"{context}: Error code={msg_cd}")
        if "output" in response_data:
            logger.debug(f"{context}: Response output={response_data['output']}")
            
        return False, error_msg


def _save_api_error_to_db(db_manager: Optional[Any], kis_auth: Optional[KISAuth], context: str, error_msg: str) -> None:
    """KIS API 최종 실패를 system_logs DB에 기록합니다. 실패해도 예외를 발생시키지 않습니다."""
    if db_manager is None:
        return
    try:
        from .db_models import SystemLogRecord
        env = kis_auth.env if kis_auth else "unknown"
        db_manager.save_system_log(SystemLogRecord(
            level='ERROR',
            module='kis_api',
            message=f"{context}: {error_msg}",
            environment=env,
            extra_data={"context": context, "error": error_msg}
        ))
    except Exception as e:
        logger.error(f"Failed to save API error to DB: {e}")


def execute_api_request_with_retry(
    method: str,
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 10,
    context: str = "KIS API",
    kis_auth: Optional[KISAuth] = None,
    max_retries: int = 3,
    base_delay: float = 1.0,
    db_manager: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Rate limiting과 백오프 전략이 적용된 KIS API 요청을 실행합니다.
    
    Args:
        method (str): HTTP 메서드 ('GET', 'POST', 'DELETE' 등)
        url (str): API 엔드포인트 URL
        headers (Dict[str, str]): 요청 헤더
        params (Dict[str, Any], optional): URL 파라미터 (GET 요청용)
        json_data (Dict[str, Any], optional): JSON 바디 (POST 요청용)
        timeout (int): 요청 타임아웃 (초)
        context (str): 에러 로그에 포함할 컨텍스트 정보
        kis_auth (KISAuth, optional): KIS 인증 정보 (환경 확인용)
        max_retries (int): 최대 재시도 횟수
        base_delay (float): 기본 지연 시간 (초)
    
    Returns:
        Dict[str, Any]: API 응답 JSON 데이터
    
    Raises:
        requests.exceptions.RequestException: HTTP 요청 실패
        RuntimeError: API 응답이 에러 상태
    """
    env = kis_auth.env if kis_auth else "demo"
    
    for attempt in range(max_retries + 1):
        try:
            # Rate limiting 지연 적용
            if attempt > 0:
                # 백오프 전략: 지수적 증가 + 지터
                backoff_delay = base_delay * (2 ** (attempt - 1))
                import random
                jitter = random.uniform(0.5, 1.5)  # 50%-150% 지터
                total_delay = backoff_delay * jitter
                logger.warning(f"{context}: Retrying in {total_delay:.2f}s (attempt {attempt}/{max_retries})")
                time.sleep(total_delay)
            else:
                # 첫 번째 호출에는 기본 rate limiting만 적용
                smart_sleep(env)
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=json_data, timeout=timeout)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            data = response.json()
            
            # API 응답 검증
            success, error_msg = validate_api_response(data, context)
            if not success:
                # 토큰 만료 에러인 경우 토큰 갱신 후 재시도
                if "EGW00123" in error_msg and kis_auth is not None:
                    logger.warning(f"{context}: Token expired, attempting refresh...")
                    try:
                        kis_auth.authenticate(force_refresh=True)
                        # 헤더 업데이트 (새로운 토큰으로)
                        headers["authorization"] = f"Bearer {kis_auth.token}"
                        logger.info(f"{context}: Token refreshed, retrying request...")
                        continue  # 재시도
                    except Exception as refresh_error:
                        logger.error(f"{context}: Token refresh failed - {refresh_error}")
                        # 토큰 갱신 실패 시 원래 에러로 처리
                        
                # Rate limiting 오류인 경우 재시도
                if "EGW00201" in error_msg or "초당 거래건수" in error_msg:
                    if attempt < max_retries:
                        logger.warning(f"{context}: Rate limit hit, will retry...")
                        continue
                _save_api_error_to_db(db_manager, kis_auth, context, error_msg)
                raise RuntimeError(f"{context} returned error: {error_msg}")
            
            return data
            
        except requests.exceptions.Timeout:
            logger.error(f"{context}: Request timeout after {timeout}s (attempt {attempt + 1})")
            if attempt >= max_retries:
                _save_api_error_to_db(db_manager, kis_auth, context, f"Request timeout after {timeout}s")
                raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"{context}: Connection error - {e} (attempt {attempt + 1})")
            if attempt >= max_retries:
                _save_api_error_to_db(db_manager, kis_auth, context, f"Connection error: {e}")
                raise
        except requests.exceptions.HTTPError as e:
            # HTTP 에러 시에도 response body에서 KIS API 에러 메시지 추출 시도
            try:
                if response.content:
                    error_data = response.json()
                    rt_cd = error_data.get('rt_cd', '')
                    msg_cd = error_data.get('msg_cd', '')
                    msg1 = error_data.get('msg1', '')
                    
                    if msg_cd or msg1:
                        detailed_error = f"[{msg_cd}] {msg1}" if msg_cd else msg1
                        
                        # 토큰 만료 에러인 경우 토큰 갱신 후 재시도
                        if "EGW00123" in detailed_error and kis_auth is not None:
                            logger.warning(f"{context}: Token expired in HTTP error, attempting refresh...")
                            try:
                                kis_auth.authenticate(force_refresh=True)
                                headers["authorization"] = f"Bearer {kis_auth.token}"
                                logger.info(f"{context}: Token refreshed, retrying request...")
                                continue
                            except Exception as refresh_error:
                                logger.error(f"{context}: Token refresh failed in HTTP error - {refresh_error}")
                        
                        # Rate limiting 오류인 경우 재시도
                        if "EGW00201" in detailed_error or "초당 거래건수" in detailed_error:
                            if attempt < max_retries:
                                logger.warning(f"{context}: Rate limit HTTP error, will retry...")
                                continue
                        
                        logger.error(f"{context}: KIS API error - {detailed_error} (HTTP {response.status_code})")
                        if attempt >= max_retries:
                            _save_api_error_to_db(db_manager, kis_auth, context, detailed_error)
                            raise RuntimeError(f"{context}: {detailed_error}")
            except (ValueError, KeyError):
                pass  # JSON 파싱 실패 시 기본 HTTP 에러 메시지 사용
            
            if attempt >= max_retries:
                logger.error(f"{context}: HTTP error - {e}")
                _save_api_error_to_db(db_manager, kis_auth, context, f"HTTP error: {e}")
                raise
        except Exception as e:
            logger.error(f"{context}: Unexpected error - {e} (attempt {attempt + 1})")
            if attempt >= max_retries:
                _save_api_error_to_db(db_manager, kis_auth, context, f"Unexpected error: {e}")
                raise
    
    # 모든 재시도 실패
    _save_api_error_to_db(db_manager, kis_auth, context, f"Failed after {max_retries} retries")
    raise RuntimeError(f"{context}: Failed after {max_retries} retries")


def execute_api_request(
    method: str,
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 10,
    context: str = "KIS API"
) -> Dict[str, Any]:
    """
    기존 호환성을 위한 래퍼 함수
    """
    return execute_api_request_with_retry(
        method, url, headers, params, json_data, timeout, context
    )

def place_stock_order(
    kis_auth: KISAuth,
    base_url: str,
    order_type: str,
    action: str,
    ticker: str,
    quantity: int,
    price: Optional[float] = None,
    order_dvsn: Optional[str] = None,
    exchange_id: str = "KRX",
    sell_type: str = "01",
    condition_price: str = ""
) -> Dict[str, Any]:
    """
    주식 주문을 실행합니다 (시장가 또는 지정가).
    
    Args:
        kis_auth (KISAuth): 인증 정보
        base_url (str): KIS API 베이스 URL
        order_type (str): 주문 유형 ('market' 또는 'limit')
        action (str): 주문 방향 ('buy' 또는 'sell')
        ticker (str): 종목코드
        quantity (int): 주문 수량
        price (float, optional): 주문 가격 (지정가 주문 시 필수)
        order_dvsn (str, optional): 주문구분 (예: '00'=지정가, '01'=시장가)
        exchange_id (str, optional): 거래소ID구분코드 (기본값: 'KRX')
        sell_type (str, optional): 매도유형 (기본값: '01')
        condition_price (str, optional): 조건가격 (스탑지정가 등)
    
    Returns:
        Dict[str, Any]: {
            'success': bool,
            'message': str,
            'order_id': str (성공 시),
            'ticker': str,
            'action': str,
            'quantity': int,
            'price': float,
            'timestamp': str
        }
    """
    try:
        # 주문 유형에 따른 주문구분 및 가격 설정
        normalized_action = action.lower()
        normalized_type = order_type.lower()

        if normalized_action not in ("buy", "sell"):
            raise ValueError(f"Unsupported action: {action}")

        if normalized_type == "market":
            order_division = order_dvsn or "01"
            order_price = "0"
        elif normalized_type == "limit":
            if price is None or price <= 0:
                raise ValueError("Limit order requires a positive price")
            order_division = order_dvsn or "00"
            order_price = str(int(price))
        else:
            raise ValueError(f"Unsupported order type: {order_type}")

        if quantity <= 0:
            raise ValueError("Order quantity must be greater than 0")

        # 주문 URL과 TR ID 설정 (현금 주문 공통)
        url = f"{base_url}/uapi/domestic-stock/v1/trading/order-cash"
        # 올바른 TR ID 사용 (신버전)
        tr_id = "TTTC0012U" if normalized_action == "buy" else "TTTC0011U"
        
        # 헤더 생성
        headers = build_api_headers(kis_auth, tr_id)
        
        # 주문구분코드 설정
        if not exchange_id:
            exchange_id = "KRX"
        
        # 주문 파라미터
        params = {
            "CANO": kis_auth.account,  # 종합계좌번호 (8자리)
            "ACNT_PRDT_CD": kis_auth.product,
            "PDNO": ticker,
            "ORD_DVSN": order_division,
            "ORD_QTY": str(int(quantity)),
            "ORD_UNPR": order_price,
            "EXCG_ID_DVSN_CD": exchange_id,
        }

        if normalized_action == "sell":
            params["SLL_TYPE"] = sell_type

        if condition_price:
            params["CNDT_PRIC"] = condition_price
        
        # API 호출 (Rate limiting과 재시도 적용)
        data = execute_api_request_with_retry(
            'POST',
            url,
            headers,
            json_data=params,
            context=f"Stock order ({order_type} {action})",
            kis_auth=kis_auth
        )
        
        # 성공 응답 파싱
        order_id = data.get('output', {}).get('odno', '')
        
        return {
            'success': True,
            'message': f'{order_type.capitalize()} order placed successfully',
            'order_id': order_id,
            'ticker': ticker,
            'action': action,
            'quantity': quantity,
            'price': price or 0,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        
    except Exception as e:
        # RuntimeError에서 KIS API 에러 메시지 추출
        error_msg = str(e)
        if isinstance(e, RuntimeError) and "KIS API error" in error_msg:
            # "Stock order (market buy): KIS API error - [에러코드] 에러메시지" 형태에서 실제 에러 메시지만 추출
            if " - " in error_msg:
                error_msg = error_msg.split(" - ", 1)[1]
        
        logger.error(f"Error placing {order_type} order for {ticker}: {error_msg}")
        return {
            'success': False,
            'message': error_msg,
            'action': action,
            'quantity': quantity,
            'price': price or 0
        }
