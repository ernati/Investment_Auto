# -*- coding: utf-8 -*-
"""
삼성전자 시장가 조회 애플리케이션

이 스크립트는 한국투자증권 Open Trading API를 사용하여
삼성전자(005930)의 현재 시장가 정보를 조회합니다.
"""

import sys
import argparse
from pathlib import Path

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent.parent / "modules"))

from kis_app_utils import (
    setup_kis_client,
    print_header,
    print_market_info,
    handle_common_errors,
    ProgressPrinter
)


@handle_common_errors
def main():
    """메인 실행 함수"""
    # 명령줄 인수 파싱
    parser = argparse.ArgumentParser(description="삼성전자 시장가 조회 프로그램")
    parser.add_argument("--demo", action="store_true", help="모의투자 모드 사용 (기본값: 실전투자)")
    args = parser.parse_args()
    
    # 환경 설정
    env = "demo" if args.demo else "real"
    
    # 진행 상황 출력 헬퍼
    progress = ProgressPrinter()
    
    # 타이틀 출력
    print_header("삼성전자 시장가 조회")
    
    # 1. 설정 로드 및 클라이언트 초기화
    progress.print_step("설정 파일 로드 및 API 인증 중...")
    client, kis_config = setup_kis_client(env)
    
    progress.print_sub_step(f"환경: {env.upper()} {'(모의투자)' if args.demo else '(실전투자)'}")
    progress.print_sub_step(f"계좌: {kis_config['account']}")
    progress.print_sub_step("인증 완료")
    
    # 2. 삼성전자 시장가 조회
    progress.print_step("삼성전자(005930) 시장가 조회 중...")
    stock_code = "005930"  # 삼성전자
    
    # 전체 데이터 조회
    df = client.inquire_price(stock_code)
    
    # 주요 정보만 추출
    market_info = client.get_market_price(stock_code)
    
    # 3. 결과 출력
    print()
    print_market_info(market_info, show_details=True)
    
    # 전체 데이터 확인 (선택사항)
    print("\n[상세 데이터]")
    print(df.to_string())


if __name__ == "__main__":
    main()
