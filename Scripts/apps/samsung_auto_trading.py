# -*- coding: utf-8 -*-
"""
Samsung Stock Auto Trading App
삼성전자 주식 1주 자동 매매 애플리케이션
- 삼성전자 주식 1주를 시장가로 매수
- 2분 대기 후 시장가로 매도
"""

import sys
import time
import argparse
from pathlib import Path

# 상위 Scripts 디렉토리를 패키지 경로에 추가
scripts_path = str(Path(__file__).parent.parent)
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from modules.kis_app_utils import (
    setup_kis_trading_client,
    print_separator,
    print_info,
    handle_common_errors
)


@handle_common_errors
def main():
    """메인 함수"""
    
    # 명령줄 인수 파싱
    parser = argparse.ArgumentParser(description="삼성전자 주식 자동 매매 프로그램")
    parser.add_argument("--demo", action="store_true", help="모의투자 모드 사용 (기본값: 실전투자)")
    args = parser.parse_args()
    
    # 환경 설정
    env = "demo" if args.demo else "real"
    
    print_separator(width=70, char="=")
    print("삼성전자 주식 자동 매매 프로그램")
    print_separator(width=70, char="=")
    
    # 설정
    STOCK_CODE = "005930"  # 삼성전자 종목코드
    STOCK_NAME = "삼성전자"
    QUANTITY = 1  # 매수/매도 수량
    WAIT_SECONDS = 120  # 대기 시간 (2분 = 120초)
    
    # 1. 설정 로드 및 클라이언트 초기화
    print_info("설정 파일을 로드합니다...")
    api_client, trading, kis_config = setup_kis_trading_client(env)
    print_info(f"환경: {env.upper()} {'(모의투자)' if args.demo else '(실전투자)'}")
    print_info(f"계좌번호: {kis_config['account']}")
    print_info("인증 완료!")
    
    print_separator(width=70, char="-")
    
    # 2. 현재가 조회
    print_info(f"{STOCK_NAME}({STOCK_CODE}) 현재가 조회 중...")
    market_info = api_client.get_market_price(STOCK_CODE)
    
    if market_info:
        current_price = market_info['현재가']
        print_info(f"현재가: {current_price}원")
        print_info(f"전일대비: {market_info['전일대비']}원 ({market_info['등락률']}%)")
    else:
        print_info("현재가를 조회할 수 없습니다.", prefix="[WARN]")
    
    print_separator(width=70, char="-")
    
    # 3. 매수 주문
    print_info(f"{STOCK_NAME} {QUANTITY}주 시장가 매수 주문 실행...")
    buy_result = trading.buy_market_order(STOCK_CODE, QUANTITY)
    
    if buy_result['success']:
        print_info("✓ 매수 주문 성공!", prefix="[SUCCESS]")
        print_info(f"  주문번호: {buy_result['order_no']}")
        print_info(f"  주문시각: {buy_result['order_time']}")
        print_info(f"  메시지: {buy_result['message']}")
    else:
        print_info(f"✗ 매수 주문 실패: {buy_result['message']}", prefix="[ERROR]")
        return
    
    print_separator(width=70, char="-")
    
    # 4. 2분 대기
    print_info(f"{WAIT_SECONDS}초 ({WAIT_SECONDS // 60}분) 대기 중...")
    
    # 10초마다 진행 상황 표시
    for i in range(WAIT_SECONDS // 10):
        time.sleep(10)
        elapsed = (i + 1) * 10
        remaining = WAIT_SECONDS - elapsed
        print_info(f"  경과: {elapsed}초 / 남은 시간: {remaining}초", prefix="[WAIT]")
    
    # 나머지 시간 대기
    remaining_seconds = WAIT_SECONDS % 10
    if remaining_seconds > 0:
        time.sleep(remaining_seconds)
    
    print_info("대기 완료!")
    
    print_separator(width=70, char="-")
    
    # 5. 매도 주문
    print_info(f"{STOCK_NAME} {QUANTITY}주 시장가 매도 주문 실행...")
    sell_result = trading.sell_market_order(STOCK_CODE, QUANTITY)
    
    if sell_result['success']:
        print_info("✓ 매도 주문 성공!", prefix="[SUCCESS]")
        print_info(f"  주문번호: {sell_result['order_no']}")
        print_info(f"  주문시각: {sell_result['order_time']}")
        print_info(f"  메시지: {sell_result['message']}")
    else:
        print_info(f"✗ 매도 주문 실패: {sell_result['message']}", prefix="[ERROR]")
        return
    
    print_separator(width=70, char="=")
    print_info("프로그램이 정상적으로 완료되었습니다.", prefix="[COMPLETE]")
    print_separator(width=70, char="=")


if __name__ == "__main__":
    main()
