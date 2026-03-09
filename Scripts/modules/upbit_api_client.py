# -*- coding: utf-8 -*-
"""
Upbit API Client Module
업비트 Open API를 통해 비트코인 거래를 수행하는 모듈

주요 기능:
- 계좌 잔고 조회 (KRW, BTC)
- 비트코인 현재가 조회  
- 비트코인 매수/매도 (시장가)
- 데모 모드 지원 (파일 기반 가상 거래 - KIS와 동일한 현금 파일 사용)
"""

import uuid
import jwt
import hashlib
import logging
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from .config_loader import get_config
from .demo_cash_manager import DemoUpbitCashManager


logger = logging.getLogger(__name__)


# Upbit API Base URL
UPBIT_BASE_URL = "https://api.upbit.com"


class UpbitAuth:
    """Upbit API 인증 정보 관리 클래스"""
    
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        env: str = "demo"
    ):
        """
        Args:
            access_key (str): Upbit API Access Key
            secret_key (str): Upbit API Secret Key
            env (str): 환경 설정 ('real' 또는 'demo')
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.env = env
        self.base_url = UPBIT_BASE_URL
        
    def get_auth_header(self, query_params: Optional[Dict] = None) -> Dict[str, str]:
        """
        인증 헤더를 생성합니다.
        
        Args:
            query_params (dict, optional): 쿼리 파라미터 (주문 등에 필요)
            
        Returns:
            dict: Authorization 헤더
        """
        payload = {
            "access_key": self.access_key,
            "nonce": str(uuid.uuid4()),
        }
        
        # 쿼리 파라미터가 있으면 해시 추가
        if query_params:
            query_string = urlencode(query_params)
            query_hash = hashlib.sha512(query_string.encode()).hexdigest()
            payload["query_hash"] = query_hash
            payload["query_hash_alg"] = "SHA512"
        
        jwt_token = jwt.encode(payload, self.secret_key, algorithm="HS256")
        
        return {
            "Authorization": f"Bearer {jwt_token}",
            "Accept": "application/json",
        }


class UpbitClient:
    """Upbit API 클라이언트"""
    
    def __init__(self, auth: UpbitAuth, account: Optional[str] = None):
        """
        Args:
            auth (UpbitAuth): 인증 정보
            account (str, optional): 계좌번호 (데모 모드에서 파일 저장에 사용)
        """
        self.auth = auth
        self.is_demo = auth.env == "demo"
        self._demo_manager: Optional[DemoUpbitCashManager] = None
        
        if self.is_demo:
            # 데모 모드: 파일 기반 DemoUpbitCashManager 사용 (KIS와 동일한 현금 파일)
            if account is None:
                # 계좌번호가 없으면 config에서 기본 KIS 계좌 사용
                config = get_config()
                kis_config = config.get_kis_config("demo")
                account = kis_config.get("account", "00000000")
            self._demo_manager = DemoUpbitCashManager(account)
        
        logger.info(f"UpbitClient 초기화: env={auth.env}, demo_mode={self.is_demo}")
    
    def get_bitcoin_price(self) -> Dict[str, Any]:
        """
        비트코인 현재가 조회 (KRW-BTC)
        
        Returns:
            dict: 비트코인 시세 정보
        """
        path = "/v1/ticker"
        params = {"markets": "KRW-BTC"}
        headers = {"Accept": "application/json"}
        
        try:
            response = requests.get(
                f"{self.auth.base_url}{path}",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    btc_data = data[0]
                    return {
                        "success": True,
                        "market": btc_data.get("market"),
                        "trade_price": btc_data.get("trade_price"),
                        "opening_price": btc_data.get("opening_price"),
                        "high_price": btc_data.get("high_price"),
                        "low_price": btc_data.get("low_price"),
                        "prev_closing_price": btc_data.get("prev_closing_price"),
                        "change_rate": btc_data.get("change_rate"),
                        "trade_volume": btc_data.get("trade_volume"),
                        "timestamp": btc_data.get("timestamp")
                    }
            
            return {"success": False, "error": f"API 오류: {response.status_code}"}
            
        except Exception as e:
            logger.error(f"비트코인 가격 조회 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        계좌 정보 조회
        
        Returns:
            dict: 계좌 정보 (KRW 및 BTC 잔고)
        """
        # 데모 모드
        if self.is_demo and self._demo_manager:
            balances = self._demo_manager.get_balances()
            return {
                "success": True,
                "krw": balances["krw"],
                "btc": balances["btc"],
                "avg_buy_price": balances["avg_buy_price"],
                "is_demo": True
            }
        
        # 실전 모드
        path = "/v1/accounts"
        headers = self.auth.get_auth_header()
        
        try:
            response = requests.get(
                f"{self.auth.base_url}{path}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                accounts = response.json()
                result = {"success": True, "krw": 0.0, "btc": 0.0, "is_demo": False}
                
                for account in accounts:
                    currency = account.get("currency")
                    balance = float(account.get("balance", 0))
                    
                    if currency == "KRW":
                        result["krw"] = balance
                    elif currency == "BTC":
                        result["btc"] = balance
                        result["avg_buy_price"] = float(account.get("avg_buy_price", 0))
                
                return result
            
            return {"success": False, "error": f"API 오류: {response.status_code}"}
            
        except Exception as e:
            logger.error(f"계좌 정보 조회 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def buy_bitcoin(self, krw_amount: float) -> Dict[str, Any]:
        """
        비트코인 매수 (시장가)
        
        Args:
            krw_amount (float): 매수할 KRW 금액
            
        Returns:
            dict: 주문 결과
        """
        # 비트코인 현재가 조회
        price_info = self.get_bitcoin_price()
        if not price_info.get("success"):
            return price_info
        
        current_price = price_info["trade_price"]
        
        # 데모 모드
        if self.is_demo and self._demo_manager:
            return self._demo_manager.buy(krw_amount, current_price)
        
        # 실전 모드
        path = "/v1/orders"
        order_data = {
            "market": "KRW-BTC",
            "side": "bid",
            "price": str(int(krw_amount)),
            "ord_type": "price"  # 시장가 (금액 지정)
        }
        
        headers = self.auth.get_auth_header(order_data)
        headers["Content-Type"] = "application/json"
        
        try:
            response = requests.post(
                f"{self.auth.base_url}{path}",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "order_id": result.get("uuid"),
                    "market": result.get("market"),
                    "side": result.get("side"),
                    "price": result.get("price"),
                    "state": result.get("state"),
                    "krw_amount": krw_amount,
                    "current_price": current_price
                }
            
            error_data = response.json() if response.content else {}
            return {
                "success": False,
                "error": error_data.get("error", {}).get("message", "주문 실패"),
                "status_code": response.status_code
            }
            
        except Exception as e:
            logger.error(f"비트코인 매수 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def sell_bitcoin(self, btc_quantity: Optional[float] = None) -> Dict[str, Any]:
        """
        비트코인 매도 (시장가)
        
        Args:
            btc_quantity (float, optional): 매도할 BTC 수량. None이면 전량 매도
            
        Returns:
            dict: 주문 결과
        """
        # 비트코인 현재가 조회
        price_info = self.get_bitcoin_price()
        if not price_info.get("success"):
            return price_info
        
        current_price = price_info["trade_price"]
        
        # 데모 모드
        if self.is_demo and self._demo_manager:
            if btc_quantity is None:
                btc_quantity = self._demo_manager.btc_balance
            return self._demo_manager.sell(btc_quantity, current_price)
        
        # 실전 모드: 수량이 지정되지 않으면 전량 조회
        if btc_quantity is None:
            account_info = self.get_account_info()
            if not account_info.get("success"):
                return account_info
            btc_quantity = account_info.get("btc", 0)
        
        if btc_quantity <= 0:
            return {"success": False, "error": "매도할 BTC가 없습니다"}
        
        path = "/v1/orders"
        order_data = {
            "market": "KRW-BTC",
            "side": "ask",
            "volume": str(btc_quantity),
            "ord_type": "market"  # 시장가
        }
        
        headers = self.auth.get_auth_header(order_data)
        headers["Content-Type"] = "application/json"
        
        try:
            response = requests.post(
                f"{self.auth.base_url}{path}",
                json=order_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "order_id": result.get("uuid"),
                    "market": result.get("market"),
                    "side": result.get("side"),
                    "volume": result.get("volume"),
                    "state": result.get("state"),
                    "btc_quantity": btc_quantity,
                    "current_price": current_price
                }
            
            error_data = response.json() if response.content else {}
            return {
                "success": False,
                "error": error_data.get("error", {}).get("message", "주문 실패"),
                "status_code": response.status_code
            }
            
        except Exception as e:
            logger.error(f"비트코인 매도 실패: {e}")
            return {"success": False, "error": str(e)}
    
    def get_btc_evaluation(self) -> Dict[str, Any]:
        """
        비트코인 평가 정보 조회
        
        Returns:
            dict: 평가 정보 (보유량, 현재가, 평가금액 등)
        """
        # 현재가 조회
        price_info = self.get_bitcoin_price()
        if not price_info.get("success"):
            return price_info
        
        current_price = price_info["trade_price"]
        
        # 데모 모드
        if self.is_demo and self._demo_manager:
            eval_info = self._demo_manager.get_evaluation(current_price)
            return {"success": True, **eval_info, "is_demo": True}
        
        # 실전 모드
        account_info = self.get_account_info()
        if not account_info.get("success"):
            return account_info
        
        btc_balance = account_info.get("btc", 0)
        btc_value = btc_balance * current_price
        krw_balance = account_info.get("krw", 0)
        
        return {
            "success": True,
            "krw_balance": krw_balance,
            "btc_balance": btc_balance,
            "btc_value": btc_value,
            "total_value": krw_balance + btc_value,
            "avg_buy_price": account_info.get("avg_buy_price", 0),
            "current_price": current_price,
            "is_demo": False
        }


# 전역 Upbit 클라이언트 인스턴스
_global_upbit_client: Optional[UpbitClient] = None


def get_upbit_client(
    env: str = "demo", 
    reload: bool = False,
    account: Optional[str] = None
) -> UpbitClient:
    """
    전역 Upbit 클라이언트 인스턴스를 가져옵니다.
    
    Args:
        env (str): 환경 설정 ('real' 또는 'demo')
        reload (bool): 클라이언트를 새로 생성할지 여부
        account (str, optional): 계좌번호 (데모 모드에서 파일 저장에 사용)
        
    Returns:
        UpbitClient: Upbit API 클라이언트
    """
    global _global_upbit_client
    
    if _global_upbit_client is None or reload:
        config = get_config()
        upbit_config = config.get_upbit_config(env)
        
        auth = UpbitAuth(
            access_key=upbit_config.get("access_key", ""),
            secret_key=upbit_config.get("secret_key", ""),
            env=env
        )
        _global_upbit_client = UpbitClient(auth, account=account)
    
    return _global_upbit_client
