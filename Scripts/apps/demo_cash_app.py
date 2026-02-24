#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Investment Auto Demo with Cash Management
모의투자용 가상 현금 관리 기능을 포함한 데모 프로그램
"""

import argparse
import logging
import sys
import os
from pprint import pprint

# 프로젝트 루트를 sys.path에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.demo_cash_manager import get_demo_cash_manager


# 로깅 설정
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def print_separator(width=70, char="-"):
    """구분선 출력"""
    print(char * width)


def print_info(message, prefix="[INFO]"):
    """정보 메시지 출력"""
    print(f"{prefix} {message}")


def show_cash_balance(account):
    """현금 잔액 정보 표시"""
    print_separator(width=70, char="=")
    print("💰 현재 계좌 잔액 정보")
    print_separator(width=70, char="=")
    
    try:
        manager = get_demo_cash_manager(account)
        cash_info = manager.get_cash_info()
        
        print(f"계좌번호: {cash_info['account']}")
        print(f"현금잔액: {cash_info['cash_balance']:,}원")
        print(f"마지막 업데이트: {cash_info['last_updated']}")
        print(f"거래 건수: {cash_info['transaction_count']}건")
        
    except Exception as e:
        print_info(f"잔액 정보 조회 실패: {e}", prefix="[ERROR]")


def simulate_buy_order(account, stock_code, quantity, price):
    """가상 매수 주문 시뮬레이션"""
    print_separator(width=70, char="=")
    print(f"📈 매수 주문 시뮬레이션")
    print_separator(width=70, char="=")
    
    try:
        manager = get_demo_cash_manager(account)
        
        print(f"종목코드: {stock_code}")
        print(f"수량: {quantity}주")
        print(f"가격: {price:,}원")
        print(f"총 주문금액: {quantity * price:,}원")
        
        print(f"\n매수 전 잔액: {manager.get_cash_balance():,}원")
        
        # 매수 실행
        success = manager.buy_stock(stock_code, quantity, price)
        
        if success:
            print_info("✅ 매수 주문 성공!", prefix="[SUCCESS]")
        else:
            print_info("❌ 매수 주문 실패! (현금 부족)", prefix="[FAILED]")
        
        print(f"매수 후 잔액: {manager.get_cash_balance():,}원")
        
    except Exception as e:
        print_info(f"매수 주문 실패: {e}", prefix="[ERROR]")


def simulate_sell_order(account, stock_code, quantity, price):
    """가상 매도 주문 시뮬레이션"""
    print_separator(width=70, char="=")
    print(f"📉 매도 주문 시뮬레이션")
    print_separator(width=70, char="=")
    
    try:
        manager = get_demo_cash_manager(account)
        
        print(f"종목코드: {stock_code}")
        print(f"수량: {quantity}주")
        print(f"가격: {price:,}원")
        print(f"총 매도금액: {quantity * price:,}원")
        
        print(f"\n매도 전 잔액: {manager.get_cash_balance():,}원")
        
        # 매도 실행
        success = manager.sell_stock(stock_code, quantity, price)
        
        if success:
            print_info("✅ 매도 주문 성공!", prefix="[SUCCESS]")
        else:
            print_info("❌ 매도 주문 실패!", prefix="[FAILED]")
        
        print(f"매도 후 잔액: {manager.get_cash_balance():,}원")
        
    except Exception as e:
        print_info(f"매도 주문 실패: {e}", prefix="[ERROR]")


def show_transaction_history(account, limit=10):
    """거래 내역 표시"""
    print_separator(width=70, char="=")
    print(f"📋 거래 내역 (최근 {limit}건)")
    print_separator(width=70, char="=")
    
    try:
        manager = get_demo_cash_manager(account)
        history = manager.get_transaction_history(limit)
        
        if not history:
            print_info("거래 내역이 없습니다.")
            return
        
        for i, tx in enumerate(history, 1):
            print(f"{i:2d}. [{tx['type']:^6}] {tx['timestamp'][:19]}")
            print(f"    금액: {tx['amount']:+10,}원 → 잔액: {tx['balance_after']:10,}원")
            if tx['stock_code']:
                print(f"    종목: {tx['stock_code']} {tx['quantity']}주 @ {tx['price']:,}원")
            if tx['memo']:
                print(f"    메모: {tx['memo']}")
            print()
        
    except Exception as e:
        print_info(f"거래 내역 조회 실패: {e}", prefix="[ERROR]")


def reset_account(account, amount=10000000):
    """계좌 초기화"""
    print_separator(width=70, char="=")
    print(f"🔄 계좌 초기화")
    print_separator(width=70, char="=")
    
    try:
        manager = get_demo_cash_manager(account)
        old_balance = manager.get_cash_balance()
        
        manager.reset_cash_balance(amount)
        
        print(f"이전 잔액: {old_balance:,}원")
        print(f"초기화 잔액: {amount:,}원")
        print_info("✅ 계좌 초기화 완료!", prefix="[SUCCESS]")
        
    except Exception as e:
        print_info(f"계좌 초기화 실패: {e}", prefix="[ERROR]")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="Investment Auto Demo with Cash Management")
    parser.add_argument("--account", default="12345678", help="계좌번호 (기본값: 12345678)")
    parser.add_argument("--action", choices=["balance", "buy", "sell", "history", "reset"], 
                       default="balance", help="실행할 작업")
    parser.add_argument("--stock", default="005930", help="종목코드 (기본값: 005930=삼성전자)")
    parser.add_argument("--quantity", type=int, default=10, help="수량 (기본값: 10)")
    parser.add_argument("--price", type=int, default=75000, help="가격 (기본값: 75000)")
    parser.add_argument("--reset-amount", type=int, default=10000000, 
                       help="초기화 금액 (기본값: 10000000)")
    
    args = parser.parse_args()
    
    print("🏛️  Investment Auto Demo - 가상 현금 관리")
    print_separator(width=70, char="=")
    print(f"계좌번호: {args.account}")
    print(f"작업: {args.action}")
    
    if args.action == "balance":
        show_cash_balance(args.account)
        
    elif args.action == "buy":
        simulate_buy_order(args.account, args.stock, args.quantity, args.price)
        
    elif args.action == "sell":
        simulate_sell_order(args.account, args.stock, args.quantity, args.price)
        
    elif args.action == "history":
        show_transaction_history(args.account)
        
    elif args.action == "reset":
        reset_account(args.account, args.reset_amount)
    
    print_separator(width=70, char="=")


if __name__ == "__main__":
    main()