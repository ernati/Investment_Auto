#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo Cash Management Test Script
모의투자 가상 현금 관리 기능 테스트용 스크립트
"""

import logging
import sys
import os
from datetime import datetime

# 프로젝트 루트를 sys.path에 추가
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.demo_cash_manager import DemoCashManager
from modules.kis_auth import KISAuth
from modules.kis_portfolio_fetcher import KISPortfolioFetcher
from modules.kis_trading import KISTrading

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_demo_cash_manager():
    """가상 현금 관리자 단독 테스트"""
    print("=" * 70)
    print("🏛️  가상 현금 관리자 단독 테스트")
    print("=" * 70)
    
    # 테스트 계좌
    test_account = "12345678"
    manager = DemoCashManager(test_account)
    
    print(f"📊 초기 잔액 정보:")
    cash_info = manager.get_cash_info()
    for key, value in cash_info.items():
        print(f"   {key}: {value}")
    
    print(f"\n💰 초기 현금 잔액: {manager.get_cash_balance():,}원")
    
    # 가상 매수 테스트
    print(f"\n📈 가상 매수 테스트: 005930 (삼성전자) 10주 @ 75,000원")
    success = manager.buy_stock("005930", 10, 75000)
    print(f"   결과: {'성공' if success else '실패'}")
    print(f"   현재 잔액: {manager.get_cash_balance():,}원")
    
    # 가상 매도 테스트
    print(f"\n📉 가상 매도 테스트: 000660 (SK하이닉스) 5주 @ 130,000원")
    success = manager.sell_stock("000660", 5, 130000)
    print(f"   결과: {'성공' if success else '실패'}")
    print(f"   현재 잔액: {manager.get_cash_balance():,}원")
    
    # 거래내역 확인
    print(f"\n📋 최근 거래내역 (최근 5건):")
    history = manager.get_transaction_history(5)
    for i, tx in enumerate(history, 1):
        print(f"   {i}. [{tx['type']}] {tx['timestamp'][:19]} "
              f"{tx['amount']:+,}원 (잔액: {tx['balance_after']:,}원)")
        if tx['stock_code']:
            print(f"      {tx['stock_code']} {tx['quantity']}주 @ {tx['price']:,}원")


def test_demo_trading_integration():
    """모의거래 통합 테스트 (실제 KIS 객체 사용 시뮬레이션)"""
    print("\n" + "=" * 70)
    print("🔄 모의거래 통합 테스트 (시뮬레이션)")
    print("=" * 70)
    
    # Mock KIS Auth 객체 생성 (실제 인증 없이 테스트용)
    class MockKISAuth:
        def __init__(self):
            self.account = "12345678"  # 테스트 계좌
            self.product = "01"
            self.env = "demo"
            self.base_url = "https://openapi.koreainvestment.com:9443"
    
    try:
        # Mock 인증 객체 생성
        mock_auth = MockKISAuth()
        print(f"🔑 Mock 인증 객체 생성: 계좌 {mock_auth.account} (환경: {mock_auth.env})")
        
        # 포트폴리오 조회 객체 생성
        portfolio_fetcher = KISPortfolioFetcher(mock_auth)
        print(f"📊 포트폴리오 조회 객체 생성 완료")
        
        # 현금 잔액 조회 (demo 환경에서는 가상 현금 관리자 사용)
        print(f"\n💰 현금 잔액 조회 (Demo 모드):")
        balance = portfolio_fetcher.fetch_account_balance()
        for key, value in balance.items():
            print(f"   {key}: {value:,}원")
        
    except Exception as e:
        print(f"❌ 통합 테스트 실패: {e}")
        print("   실제 KIS API 인증이 필요한 기능입니다.")


def test_cash_insufficient_scenario():
    """현금 부족 시나리오 테스트"""
    print("\n" + "=" * 70)
    print("⚠️  현금 부족 시나리오 테스트")
    print("=" * 70)
    
    test_account = "99999999"  # 별도 테스트 계좌
    manager = DemoCashManager(test_account)
    
    print(f"💰 초기 현금 잔액: {manager.get_cash_balance():,}원")
    
    # 초기 잔액을 100만원으로 설정
    manager.reset_cash_balance(1000000)
    print(f"🔄 잔액 리셋: {manager.get_cash_balance():,}원")
    
    # 잔액보다 많은 금액 매수 시도
    print(f"\n📈 잔액 초과 매수 시도: 005930 20주 @ 75,000원 (총 1,500,000원)")
    success = manager.buy_stock("005930", 20, 75000)
    print(f"   결과: {'성공' if success else '실패 (현금 부족)'}")
    print(f"   현재 잔액: {manager.get_cash_balance():,}원")
    
    # 적정 금액으로 매수 시도
    print(f"\n📈 적정 금액 매수 시도: 005930 10주 @ 75,000원 (총 750,000원)")
    success = manager.buy_stock("005930", 10, 75000)
    print(f"   결과: {'성공' if success else '실패'}")
    print(f"   현재 잔액: {manager.get_cash_balance():,}원")


def main():
    """메인 테스트 함수"""
    print("🏛️  Investment_Auto Demo Cash Management 테스트")
    print("=" * 70)
    print(f"테스트 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 1. 가상 현금 관리자 단독 테스트
        test_demo_cash_manager()
        
        # 2. 통합 테스트 (시뮬레이션)
        test_demo_trading_integration()
        
        # 3. 현금 부족 시나리오 테스트
        test_cash_insufficient_scenario()
        
        print("\n" + "=" * 70)
        print("✅ 모든 테스트 완료!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()