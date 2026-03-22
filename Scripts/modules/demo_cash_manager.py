# -*- coding: utf-8 -*-
"""
Demo Cash Manager Module
모의투자환경에서 가상 현금 잔액을 관리하는 모듈
"""

import os
import json
import logging
from typing import Dict, Any
from datetime import datetime


logger = logging.getLogger(__name__)


class DemoCashManager:
    """모의투자용 가상 현금 관리 클래스"""
    
    def __init__(self, account: str):
        """
        Args:
            account (str): 계좌번호
        """
        self.account = account
        self.data_dir = os.path.join(os.path.dirname(__file__), "demo_data")
        self.cash_file = os.path.join(self.data_dir, f"cash_{account}.json")
        self._ensure_data_dir()
        self._init_cash_balance()
    
    def _ensure_data_dir(self):
        """데이터 디렉토리가 존재하지 않으면 생성합니다."""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            logger.info(f"Demo 데이터 디렉토리 생성: {self.data_dir}")
    
    def _init_cash_balance(self):
        """초기 현금 잔액을 설정합니다."""
        if not os.path.exists(self.cash_file):
            initial_data = {
                "account": self.account,
                "cash_balance": 10000000,  # 초기 1000만원
                "upbit_krw_balance": 2000000,  # Upbit 초기 200만원
                "upbit_btc_balance": 0.0,  # Upbit 초기 BTC 0
                "upbit_avg_buy_price": 0.0,  # Upbit BTC 평균 매수가
                "overseas_balances": {  # 해외주식 외화 잔고
                    "USD": {"balance": 10000.00, "avg_exchange_rate": 0.0},
                    "JPY": {"balance": 500000, "avg_exchange_rate": 0.0},
                    "HKD": {"balance": 50000.00, "avg_exchange_rate": 0.0},
                    "CNY": {"balance": 10000.00, "avg_exchange_rate": 0.0},
                    "VND": {"balance": 50000000, "avg_exchange_rate": 0.0}
                },
                "overseas_holdings": {},  # 해외주식 보유 현황
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "transaction_history": [],
                "upbit_transaction_history": [],
                "overseas_transaction_history": []
            }
            self._save_data(initial_data)
            logger.info(f"초기 계좌 현금 잔액 설정: {initial_data['cash_balance']:,}원 (계좌: {self.account})")
            logger.info(f"초기 Upbit 잔액 설정: KRW={initial_data['upbit_krw_balance']:,}원, BTC={initial_data['upbit_btc_balance']}")
            logger.info(f"초기 해외 외화 잔고 설정: USD={initial_data['overseas_balances']['USD']['balance']:,.2f}")
        else:
            # 기존 파일에 필수 필드가 없으면 추가
            data = self._load_data()
            updated = False
            
            if "upbit_krw_balance" not in data:
                data["upbit_krw_balance"] = 2000000
                updated = True
            if "upbit_btc_balance" not in data:
                data["upbit_btc_balance"] = 0.0
                updated = True
            if "upbit_avg_buy_price" not in data:
                data["upbit_avg_buy_price"] = 0.0
                updated = True
            if "upbit_transaction_history" not in data:
                data["upbit_transaction_history"] = []
                updated = True
            
            # 해외주식 필드 추가
            if "overseas_balances" not in data:
                data["overseas_balances"] = {
                    "USD": {"balance": 10000.00, "avg_exchange_rate": 0.0},
                    "JPY": {"balance": 500000, "avg_exchange_rate": 0.0},
                    "HKD": {"balance": 50000.00, "avg_exchange_rate": 0.0},
                    "CNY": {"balance": 10000.00, "avg_exchange_rate": 0.0},
                    "VND": {"balance": 50000000, "avg_exchange_rate": 0.0}
                }
                updated = True
                logger.info(f"기존 cash 파일에 해외 외화 잔고 필드 추가됨")
            if "overseas_holdings" not in data:
                data["overseas_holdings"] = {}
                updated = True
            if "overseas_transaction_history" not in data:
                data["overseas_transaction_history"] = []
                updated = True
            
            if updated:
                self._save_data(data)
                logger.info(f"기존 cash 파일 필드 업데이트 완료")
    
    def _load_data(self) -> Dict[str, Any]:
        """현금 데이터를 로드합니다."""
        try:
            with open(self.cash_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"현금 데이터 로드 실패: {e}")
            return {}
    
    def _save_data(self, data: Dict[str, Any]):
        """현금 데이터를 저장합니다."""
        try:
            with open(self.cash_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"현금 데이터 저장 실패: {e}")
            raise
    
    def get_cash_balance(self) -> float:
        """현재 현금 잔액을 반환합니다."""
        data = self._load_data()
        return float(data.get("cash_balance", 0))
    
    def get_cash_info(self) -> Dict[str, Any]:
        """현금 관련 전체 정보를 반환합니다."""
        data = self._load_data()
        return {
            "cash_balance": float(data.get("cash_balance", 0)),
            "account": data.get("account", ""),
            "last_updated": data.get("updated_at", ""),
            "transaction_count": len(data.get("transaction_history", []))
        }
    
    def update_cash(self, amount: float, transaction_type: str, 
                   stock_code: str = "", quantity: int = 0, 
                   price: float = 0, memo: str = "") -> bool:
        """
        현금 잔액을 업데이트합니다.
        
        Args:
            amount (float): 변경할 금액 (양수: 증가, 음수: 차감)
            transaction_type (str): 거래 유형 ("buy", "sell", "adjust")
            stock_code (str): 종목코드 (선택)
            quantity (int): 주문수량 (선택)
            price (float): 주문가격 (선택)
            memo (str): 메모 (선택)
            
        Returns:
            bool: 업데이트 성공 여부
        """
        try:
            data = self._load_data()
            current_balance = float(data.get("cash_balance", 0))
            new_balance = current_balance + amount
            
            # 현금 부족 체크 (차감하는 경우)
            if amount < 0 and new_balance < 0:
                logger.warning(f"현금 부족: 현재잔액 {current_balance:,}원, 요청금액 {abs(amount):,}원")
                return False
            
            # 거래 기록 추가
            transaction = {
                "timestamp": datetime.now().isoformat(),
                "type": transaction_type,
                "amount": amount,
                "balance_before": current_balance,
                "balance_after": new_balance,
                "stock_code": stock_code,
                "quantity": quantity,
                "price": price,
                "memo": memo
            }
            
            data["cash_balance"] = new_balance
            data["updated_at"] = datetime.now().isoformat()
            data.setdefault("transaction_history", []).append(transaction)
            
            self._save_data(data)
            
            logger.info(f"현금 잔액 업데이트: {current_balance:,}원 → {new_balance:,}원 "
                       f"(변경: {amount:+,}원, 유형: {transaction_type})")
            
            return True
            
        except Exception as e:
            logger.error(f"현금 업데이트 실패: {e}")
            return False
    
    def buy_stock(self, stock_code: str, quantity: int, price: float) -> bool:
        """
        주식 매수 시 현금을 차감합니다.
        
        Args:
            stock_code (str): 종목코드
            quantity (int): 주문수량
            price (float): 주문가격
            
        Returns:
            bool: 차감 성공 여부
        """
        total_amount = quantity * price
        return self.update_cash(
            amount=-total_amount,
            transaction_type="buy",
            stock_code=stock_code,
            quantity=quantity,
            price=price,
            memo=f"{stock_code} {quantity}주 매수"
        )
    
    def sell_stock(self, stock_code: str, quantity: int, price: float) -> bool:
        """
        주식 매도 시 현금을 증가시킵니다.
        
        Args:
            stock_code (str): 종목코드
            quantity (int): 주문수량
            price (float): 주문가격
            
        Returns:
            bool: 증가 성공 여부
        """
        total_amount = quantity * price
        return self.update_cash(
            amount=total_amount,
            transaction_type="sell",
            stock_code=stock_code,
            quantity=quantity,
            price=price,
            memo=f"{stock_code} {quantity}주 매도"
        )
    
    def get_transaction_history(self, limit: int = 50) -> list:
        """
        거래 내역을 반환합니다.
        
        Args:
            limit (int): 반환할 최대 건수
            
        Returns:
            list: 거래 내역 리스트 (최신순)
        """
        data = self._load_data()
        history = data.get("transaction_history", [])
        return list(reversed(history))[-limit:]
    
    def reset_cash_balance(self, new_balance: float = 10000000):
        """
        현금 잔액을 초기화합니다.
        
        Args:
            new_balance (float): 새로운 잔액 (기본값: 1000만원)
        """
        data = self._load_data()
        old_balance = data.get("cash_balance", 0)
        
        data["cash_balance"] = new_balance
        data["updated_at"] = datetime.now().isoformat()
        
        # 리셋 기록 추가
        reset_transaction = {
            "timestamp": datetime.now().isoformat(),
            "type": "reset",
            "amount": new_balance - old_balance,
            "balance_before": old_balance,
            "balance_after": new_balance,
            "stock_code": "",
            "quantity": 0,
            "price": 0,
            "memo": "현금 잔액 리셋"
        }
        data.setdefault("transaction_history", []).append(reset_transaction)
        
        self._save_data(data)
        logger.info(f"현금 잔액 리셋: {old_balance:,}원 → {new_balance:,}원")


def get_demo_cash_manager(account: str) -> DemoCashManager:
    """
    계좌별 가상 현금 관리자 인스턴스를 반환합니다.
    
    Args:
        account (str): 계좌번호
        
    Returns:
        DemoCashManager: 가상 현금 관리자 인스턴스
    """
    return DemoCashManager(account)


class DemoUpbitCashManager:
    """
    데모 모드용 Upbit 가상 현금/비트코인 관리 클래스
    DemoCashManager와 동일한 파일을 사용하여 영속성 제공
    """
    
    def __init__(self, account: str):
        """
        Args:
            account (str): 계좌번호 (KIS 계좌와 동일)
        """
        self.account = account
        self._cash_manager = get_demo_cash_manager(account)
        
        # 초기 잔액 로드
        data = self._cash_manager._load_data()
        self.krw_balance = float(data.get("upbit_krw_balance", 2000000))
        self.btc_balance = float(data.get("upbit_btc_balance", 0.0))
        self.buy_price = float(data.get("upbit_avg_buy_price", 0.0))
        
        logger.info(
            f"DemoUpbitCashManager 초기화 (파일 기반): "
            f"KRW={self.krw_balance:,.0f}, BTC={self.btc_balance:.8f}"
        )
    
    def _save_to_file(self):
        """현재 Upbit 잔액을 파일에 저장"""
        data = self._cash_manager._load_data()
        data["upbit_krw_balance"] = self.krw_balance
        data["upbit_btc_balance"] = self.btc_balance
        data["upbit_avg_buy_price"] = self.buy_price
        data["updated_at"] = datetime.now().isoformat()
        self._cash_manager._save_data(data)
    
    def get_balances(self) -> Dict[str, float]:
        """현재 잔액 반환"""
        return {
            "krw": self.krw_balance,
            "btc": self.btc_balance,
            "avg_buy_price": self.buy_price
        }
    
    def buy(self, krw_amount: float, current_price: float) -> Dict[str, Any]:
        """
        가상 비트코인 매수
        
        Args:
            krw_amount (float): 매수할 KRW 금액
            current_price (float): 현재 비트코인 가격
            
        Returns:
            dict: 거래 결과
        """
        if krw_amount > self.krw_balance:
            return {
                "success": False,
                "error": f"잔액 부족: {self.krw_balance:,.0f} < {krw_amount:,.0f}"
            }
        
        # 수수료 (0.05%)
        fee_rate = 0.0005
        net_amount = krw_amount * (1 - fee_rate)
        btc_quantity = net_amount / current_price
        
        # 평균 매수가 계산
        if self.btc_balance > 0:
            total_cost = (self.btc_balance * self.buy_price) + net_amount
            total_btc = self.btc_balance + btc_quantity
            self.buy_price = total_cost / total_btc
        else:
            self.buy_price = current_price
        
        # 잔고 업데이트
        self.krw_balance -= krw_amount
        self.btc_balance += btc_quantity
        
        # 파일에 저장
        self._save_to_file()
        
        # 거래 기록 추가
        self._add_transaction({
            "type": "buy",
            "krw_amount": krw_amount,
            "btc_quantity": btc_quantity,
            "price": current_price,
            "fee": krw_amount * fee_rate,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(
            f"[DEMO] BUY: {btc_quantity:.8f} BTC @ {current_price:,.0f}, "
            f"잔액: KRW={self.krw_balance:,.0f}, BTC={self.btc_balance:.8f}"
        )
        
        return {
            "success": True,
            "btc_quantity": btc_quantity,
            "krw_spent": krw_amount,
            "price": current_price,
            "fee": krw_amount * fee_rate,
            "remaining_krw": self.krw_balance,
            "total_btc": self.btc_balance
        }
    
    def sell(self, btc_quantity: float, current_price: float) -> Dict[str, Any]:
        """
        가상 비트코인 매도
        
        Args:
            btc_quantity (float): 매도할 BTC 수량
            current_price (float): 현재 비트코인 가격
            
        Returns:
            dict: 거래 결과
        """
        if btc_quantity > self.btc_balance:
            return {
                "success": False,
                "error": f"BTC 잔액 부족: {self.btc_balance:.8f} < {btc_quantity:.8f}"
            }
        
        # 수수료 (0.05%)
        fee_rate = 0.0005
        gross_amount = btc_quantity * current_price
        net_amount = gross_amount * (1 - fee_rate)
        
        # 손익 계산
        cost_basis = btc_quantity * self.buy_price
        pnl = net_amount - cost_basis
        
        # 잔고 업데이트
        self.krw_balance += net_amount
        self.btc_balance -= btc_quantity
        
        # BTC가 0이면 평균 매수가 초기화
        if self.btc_balance <= 0:
            self.btc_balance = 0.0
            self.buy_price = 0.0
        
        # 파일에 저장
        self._save_to_file()
        
        # 거래 기록 추가
        self._add_transaction({
            "type": "sell",
            "btc_quantity": btc_quantity,
            "krw_received": net_amount,
            "price": current_price,
            "fee": gross_amount * fee_rate,
            "pnl": pnl,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.info(
            f"[DEMO] SELL: {btc_quantity:.8f} BTC @ {current_price:,.0f}, "
            f"PnL={pnl:+,.0f}, 잔액: KRW={self.krw_balance:,.0f}, BTC={self.btc_balance:.8f}"
        )
        
        return {
            "success": True,
            "btc_quantity": btc_quantity,
            "krw_received": net_amount,
            "price": current_price,
            "fee": gross_amount * fee_rate,
            "pnl": pnl,
            "remaining_krw": self.krw_balance,
            "remaining_btc": self.btc_balance
        }
    
    def _add_transaction(self, record: Dict[str, Any]):
        """Upbit 거래 기록 추가"""
        data = self._cash_manager._load_data()
        if "upbit_transaction_history" not in data:
            data["upbit_transaction_history"] = []
        data["upbit_transaction_history"].append(record)
        self._cash_manager._save_data(data)
    
    def get_evaluation(self, current_price: float) -> Dict[str, float]:
        """
        현재 평가액 계산
        
        Args:
            current_price (float): 현재 비트코인 가격
            
        Returns:
            dict: 평가 정보
        """
        btc_value = self.btc_balance * current_price
        total_value = self.krw_balance + btc_value
        
        return {
            "krw_balance": self.krw_balance,
            "btc_balance": self.btc_balance,
            "btc_value": btc_value,
            "total_value": total_value,
            "avg_buy_price": self.buy_price,
            "current_price": current_price
        }
    
    def get_transaction_history(self, limit: int = 50) -> list:
        """
        Upbit 거래 내역을 반환합니다.
        
        Args:
            limit (int): 반환할 최대 건수
            
        Returns:
            list: 거래 내역 리스트 (최신순)
        """
        data = self._cash_manager._load_data()
        history = data.get("upbit_transaction_history", [])
        return list(reversed(history))[-limit:]


def get_demo_upbit_cash_manager(account: str) -> DemoUpbitCashManager:
    """
    계좌별 Upbit 가상 현금 관리자 인스턴스를 반환합니다.
    
    Args:
        account (str): 계좌번호
        
    Returns:
        DemoUpbitCashManager: Upbit 가상 현금 관리자 인스턴스
    """
    return DemoUpbitCashManager(account)


# 해외주식 통화별 초기 잔고 (USD 기준)
OVERSEAS_INITIAL_BALANCES = {
    "USD": 10000.00,   # 미국 달러 $10,000
    "JPY": 500000,     # 일본 엔 ¥500,000
    "HKD": 50000.00,   # 홍콩 달러 HK$50,000
    "CNY": 10000.00,   # 중국 위안 ¥10,000
    "VND": 50000000,   # 베트남 동 50,000,000 VND
}

# 거래소 코드별 통화 매핑
EXCHANGE_CURRENCY_MAP = {
    "NASD": "USD", "NYSE": "USD", "AMEX": "USD", "NAS": "USD",
    "SEHK": "HKD",
    "SHAA": "CNY", "SZAA": "CNY",
    "TKSE": "JPY",
    "HASE": "VND", "VNSE": "VND",
}


class DemoOverseasCashManager:
    """
    데모 모드용 해외주식 외화 잔고 관리 클래스
    DemoCashManager와 동일한 파일을 사용하여 영속성 제공
    """
    
    def __init__(self, account: str):
        """
        Args:
            account (str): 계좌번호 (KIS 계좌와 동일)
        """
        self.account = account
        self._cash_manager = get_demo_cash_manager(account)
        self._ensure_overseas_fields()
        
        logger.info(f"DemoOverseasCashManager 초기화 (계좌: {account})")
    
    def _ensure_overseas_fields(self):
        """해외주식 관련 필드가 없으면 초기화합니다."""
        data = self._cash_manager._load_data()
        updated = False
        
        # overseas_balances 필드 초기화
        if "overseas_balances" not in data:
            data["overseas_balances"] = {}
            for currency, initial_balance in OVERSEAS_INITIAL_BALANCES.items():
                data["overseas_balances"][currency] = {
                    "balance": initial_balance,
                    "avg_exchange_rate": 0.0  # 환전 시 업데이트
                }
            updated = True
            logger.info(f"해외 외화 잔고 초기화 완료")
        
        # overseas_holdings 필드 초기화
        if "overseas_holdings" not in data:
            data["overseas_holdings"] = {}
            updated = True
        
        # overseas_transaction_history 필드 초기화
        if "overseas_transaction_history" not in data:
            data["overseas_transaction_history"] = []
            updated = True
        
        if updated:
            data["updated_at"] = datetime.now().isoformat()
            self._cash_manager._save_data(data)
    
    def get_currency_for_exchange(self, exchange_code: str) -> str:
        """거래소 코드에 대한 통화 코드를 반환합니다."""
        return EXCHANGE_CURRENCY_MAP.get(exchange_code.upper(), "USD")
    
    def get_balance(self, currency: str) -> float:
        """특정 통화의 잔고를 반환합니다."""
        data = self._cash_manager._load_data()
        balances = data.get("overseas_balances", {})
        currency_data = balances.get(currency.upper(), {})
        return float(currency_data.get("balance", 0))
    
    def get_all_balances(self) -> Dict[str, Dict[str, float]]:
        """모든 외화 잔고를 반환합니다."""
        data = self._cash_manager._load_data()
        return data.get("overseas_balances", {})
    
    def get_holdings(self) -> Dict[str, Dict[str, Any]]:
        """해외 주식 보유 현황을 반환합니다."""
        data = self._cash_manager._load_data()
        return data.get("overseas_holdings", {})
    
    def buy_stock(
        self,
        stock_code: str,
        exchange_code: str,
        quantity: int,
        price: float
    ) -> Dict[str, Any]:
        """
        해외주식 매수 시 외화 잔고를 차감하고 보유 종목을 업데이트합니다.
        
        Args:
            stock_code (str): 종목코드 (예: "AAPL")
            exchange_code (str): 해외거래소코드 (예: "NASD")
            quantity (int): 주문수량
            price (float): 체결가격 (해당 통화 기준)
            
        Returns:
            dict: 처리 결과
        """
        currency = self.get_currency_for_exchange(exchange_code)
        total_cost = quantity * price
        
        data = self._cash_manager._load_data()
        balances = data.get("overseas_balances", {})
        holdings = data.get("overseas_holdings", {})
        
        # 잔고 확인
        current_balance = float(balances.get(currency, {}).get("balance", 0))
        if current_balance < total_cost:
            logger.warning(
                f"[DEMO] 해외주식 매수 실패 - {currency} 잔고 부족: "
                f"{current_balance:,.2f} < {total_cost:,.2f}"
            )
            return {
                "success": False,
                "error": f"{currency} 잔고 부족: {current_balance:,.2f} < {total_cost:,.2f}"
            }
        
        # 잔고 차감
        balances[currency]["balance"] = current_balance - total_cost
        
        # 보유 종목 업데이트 (평균 단가 계산)
        stock_key = stock_code.upper()
        if stock_key in holdings:
            existing = holdings[stock_key]
            old_qty = existing.get("quantity", 0)
            old_avg = existing.get("avg_price", 0)
            new_qty = old_qty + quantity
            new_avg = ((old_qty * old_avg) + (quantity * price)) / new_qty if new_qty > 0 else 0
            holdings[stock_key]["quantity"] = new_qty
            holdings[stock_key]["avg_price"] = round(new_avg, 4)
        else:
            holdings[stock_key] = {
                "exchange": exchange_code.upper(),
                "quantity": quantity,
                "avg_price": round(price, 4),
                "currency": currency
            }
        
        # 거래 내역 추가
        transaction = {
            "type": "buy",
            "stock_code": stock_code.upper(),
            "exchange": exchange_code.upper(),
            "quantity": quantity,
            "price": price,
            "currency": currency,
            "total_cost": total_cost,
            "balance_after": balances[currency]["balance"],
            "timestamp": datetime.now().isoformat()
        }
        
        data["overseas_balances"] = balances
        data["overseas_holdings"] = holdings
        data.setdefault("overseas_transaction_history", []).append(transaction)
        data["updated_at"] = datetime.now().isoformat()
        
        self._cash_manager._save_data(data)
        
        logger.info(
            f"[DEMO] 해외주식 매수: {stock_code} {quantity}주 @ {price:,.2f} {currency} "
            f"= {total_cost:,.2f} {currency}, 잔고: {balances[currency]['balance']:,.2f} {currency}"
        )
        
        return {
            "success": True,
            "stock_code": stock_code.upper(),
            "exchange": exchange_code.upper(),
            "quantity": quantity,
            "price": price,
            "total_cost": total_cost,
            "currency": currency,
            "remaining_balance": balances[currency]["balance"]
        }
    
    def sell_stock(
        self,
        stock_code: str,
        exchange_code: str,
        quantity: int,
        price: float
    ) -> Dict[str, Any]:
        """
        해외주식 매도 시 외화 잔고를 증가시키고 보유 종목을 업데이트합니다.
        
        Args:
            stock_code (str): 종목코드 (예: "AAPL")
            exchange_code (str): 해외거래소코드 (예: "NASD")
            quantity (int): 주문수량
            price (float): 체결가격 (해당 통화 기준)
            
        Returns:
            dict: 처리 결과
        """
        currency = self.get_currency_for_exchange(exchange_code)
        total_proceeds = quantity * price
        
        data = self._cash_manager._load_data()
        balances = data.get("overseas_balances", {})
        holdings = data.get("overseas_holdings", {})
        
        # 보유 확인
        stock_key = stock_code.upper()
        if stock_key not in holdings:
            logger.warning(f"[DEMO] 해외주식 매도 실패 - 보유 종목 없음: {stock_code}")
            return {
                "success": False,
                "error": f"보유 종목 없음: {stock_code}"
            }
        
        existing = holdings[stock_key]
        current_qty = existing.get("quantity", 0)
        avg_price = existing.get("avg_price", 0)
        
        if current_qty < quantity:
            logger.warning(
                f"[DEMO] 해외주식 매도 실패 - 보유 수량 부족: "
                f"{current_qty} < {quantity}"
            )
            return {
                "success": False,
                "error": f"보유 수량 부족: {current_qty} < {quantity}"
            }
        
        # 손익 계산
        cost_basis = quantity * avg_price
        pnl = total_proceeds - cost_basis
        pnl_rate = (pnl / cost_basis * 100) if cost_basis > 0 else 0
        
        # 잔고 증가
        if currency not in balances:
            balances[currency] = {"balance": 0, "avg_exchange_rate": 0}
        current_balance = float(balances[currency].get("balance", 0))
        balances[currency]["balance"] = current_balance + total_proceeds
        
        # 보유 수량 감소
        new_qty = current_qty - quantity
        if new_qty <= 0:
            del holdings[stock_key]
        else:
            holdings[stock_key]["quantity"] = new_qty
        
        # 거래 내역 추가
        transaction = {
            "type": "sell",
            "stock_code": stock_code.upper(),
            "exchange": exchange_code.upper(),
            "quantity": quantity,
            "price": price,
            "currency": currency,
            "total_proceeds": total_proceeds,
            "cost_basis": cost_basis,
            "pnl": pnl,
            "pnl_rate": round(pnl_rate, 2),
            "balance_after": balances[currency]["balance"],
            "timestamp": datetime.now().isoformat()
        }
        
        data["overseas_balances"] = balances
        data["overseas_holdings"] = holdings
        data.setdefault("overseas_transaction_history", []).append(transaction)
        data["updated_at"] = datetime.now().isoformat()
        
        self._cash_manager._save_data(data)
        
        logger.info(
            f"[DEMO] 해외주식 매도: {stock_code} {quantity}주 @ {price:,.2f} {currency} "
            f"= {total_proceeds:,.2f} {currency}, PnL: {pnl:+,.2f} ({pnl_rate:+.2f}%), "
            f"잔고: {balances[currency]['balance']:,.2f} {currency}"
        )
        
        return {
            "success": True,
            "stock_code": stock_code.upper(),
            "exchange": exchange_code.upper(),
            "quantity": quantity,
            "price": price,
            "total_proceeds": total_proceeds,
            "pnl": pnl,
            "pnl_rate": pnl_rate,
            "currency": currency,
            "remaining_balance": balances[currency]["balance"]
        }
    
    def get_transaction_history(self, limit: int = 50) -> list:
        """
        해외주식 거래 내역을 반환합니다.
        
        Args:
            limit (int): 반환할 최대 건수
            
        Returns:
            list: 거래 내역 리스트 (최신순)
        """
        data = self._cash_manager._load_data()
        history = data.get("overseas_transaction_history", [])
        return list(reversed(history))[-limit:]
    
    def reset_balances(self):
        """모든 해외 잔고를 초기화합니다."""
        data = self._cash_manager._load_data()
        
        # 잔고 초기화
        data["overseas_balances"] = {}
        for currency, initial_balance in OVERSEAS_INITIAL_BALANCES.items():
            data["overseas_balances"][currency] = {
                "balance": initial_balance,
                "avg_exchange_rate": 0.0
            }
        
        # 보유 종목 초기화
        data["overseas_holdings"] = {}
        
        # 거래 내역에 리셋 기록 추가
        reset_transaction = {
            "type": "reset",
            "timestamp": datetime.now().isoformat(),
            "memo": "해외 잔고 및 보유 종목 초기화"
        }
        data.setdefault("overseas_transaction_history", []).append(reset_transaction)
        data["updated_at"] = datetime.now().isoformat()
        
        self._cash_manager._save_data(data)
        logger.info(f"[DEMO] 해외 잔고 및 보유 종목 초기화 완료")


def get_demo_overseas_cash_manager(account: str) -> DemoOverseasCashManager:
    """
    계좌별 해외주식 가상 현금 관리자 인스턴스를 반환합니다.
    
    Args:
        account (str): 계좌번호
        
    Returns:
        DemoOverseasCashManager: 해외주식 가상 현금 관리자 인스턴스
    """
    return DemoOverseasCashManager(account)