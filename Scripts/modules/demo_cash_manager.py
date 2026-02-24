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
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "transaction_history": []
            }
            self._save_data(initial_data)
            logger.info(f"초기 계좌 현금 잔액 설정: {initial_data['cash_balance']:,}원 (계좌: {self.account})")
    
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