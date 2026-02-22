# -*- coding: utf-8 -*-
"""
Bond Trading Demo Application
장내채권 거래 데모 애플리케이션
- 삼성전자 채권(KR6095572D81) 1구좌 매수/매도 데모
"""

import sys
import argparse
from pathlib import Path

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent.parent / "modules"))

from config_loader import get_config
from kis_auth import KISAuth
from kis_bond_trading import KISBondTrading


def print_separator(width=70, char="="):
    """구분선 출력"""
    print(char * width)


def print_info(message):
    """정보 메시지 출력"""
    print(f"📍 {message}")


def main():
    """메인 함수"""
    
    # 명령줄 인수 파싱
    parser = argparse.ArgumentParser(description="장내채권 거래 데모 프로그램")
    parser.add_argument("--demo", action="store_true", help="모의투자 모드 사용 (기본값: 실전투자)")
    parser.add_argument("--action", choices=["buy", "sell", "info"], default="info", 
                       help="실행할 작업 (기본값: info - 채권 정보 조회)")
    parser.add_argument("--quantity", type=int, default=1, help="주문수량 (기본값: 1)")
    parser.add_argument("--price", type=str, default="10000", help="주문단가 (기본값: 10000)")
    args = parser.parse_args()
    
    # 환경 설정
    env = "demo" if args.demo else "real"
    
    print_separator(width=70, char="=")
    print("🏛️  장내채권 거래 데모 프로그램")
    print_separator(width=70, char="=")
    
    # 설정
    BOND_CODE = "KR103502GA34"  # 한국은행 통화안정증권 (테스트용)
    BOND_NAME = "한국은행통안증권"
    
    # 1. 설정 로드 및 클라이언트 초기화
    print_info("설정 파일을 로드합니다...")
    config = get_config()
    kis_config = config.get_kis_config(env)
    
    print_info(f"환경: {env.upper()} {'(모의투자)' if args.demo else '(실전투자)'}")
    print_info(f"계좌번호: {kis_config['account']}")
    
    # 2. 인증
    print_info("KIS API 인증 중...")
    auth = KISAuth(
        appkey=kis_config['appkey'],
        appsecret=kis_config['appsecret'],
        account=kis_config['account'],
        product=kis_config['product'],
        htsid=kis_config.get('htsid', ''),
        env=env
    )
    auth.authenticate()
    print_info("인증 완료!")
    
    # 3. 채권 거래 객체 생성
    bond_trading = KISBondTrading(auth)
    
    print_separator(width=70, char="-")
    
    # 4. 작업 수행
    if args.action == "info":
        # 채권 정보 조회
        print_info(f"{BOND_NAME}({BOND_CODE}) 정보 조회 중...")
        bond_info = bond_trading.get_bond_info(BOND_CODE)
        
        if bond_info['success']:
            print("✅ 채권 정보 조회 성공!")
            print(f"📄 응답 데이터: {bond_info['data']}")
        else:
            print(f"❌ 채권 정보 조회 실패: {bond_info['message']}")
            
    elif args.action == "buy":
        # 채권 매수
        print_info(f"{BOND_NAME}({BOND_CODE}) {args.quantity}구좌 매수 주문 중...")
        print_info(f"주문단가: {args.price}")
        
        if not args.demo:
            confirmation = input("⚠️  실전투자 모드입니다. 실제 거래가 실행됩니다. 계속하시겠습니까? (y/N): ")
            if confirmation.lower() != 'y':
                print("거래를 취소했습니다.")
                return
        
        result = bond_trading.buy_bond(BOND_CODE, args.quantity, args.price)
        
        if result['success']:
            print("✅ 채권 매수 주문 성공!")
            print(f"📄 주문번호: {result['order_no']}")
            print(f"📄 주문시각: {result['order_time']}")
            print(f"📄 메시지: {result['message']}")
        else:
            print(f"❌ 채권 매수 주문 실패: {result['message']}")
            
    elif args.action == "sell":
        # 채권 매도
        print_info(f"{BOND_NAME}({BOND_CODE}) {args.quantity}구좌 매도 주문 중...")
        print_info(f"주문단가: {args.price}")
        
        if not args.demo:
            confirmation = input("⚠️  실전투자 모드입니다. 실제 거래가 실행됩니다. 계속하시겠습니까? (y/N): ")
            if confirmation.lower() != 'y':
                print("거래를 취소했습니다.")
                return
        
        result = bond_trading.sell_bond(BOND_CODE, args.quantity, args.price)
        
        if result['success']:
            print("✅ 채권 매도 주문 성공!")
            print(f"📄 주문번호: {result['order_no']}")
            print(f"📄 주문시각: {result['order_time']}")
            print(f"📄 메시지: {result['message']}")
        else:
            print(f"❌ 채권 매도 주문 실패: {result['message']}")
    
    print_separator(width=70, char="=")
    print("프로그램이 완료되었습니다.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()