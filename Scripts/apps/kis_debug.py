# -*- coding: utf-8 -*-
"""
KIS API 디버깅 및 테스트 스크립트
주식 거래 실패 문제 진단용
"""

import sys
import logging
from pathlib import Path

# Scripts 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.config_loader import get_config
from modules.kis_auth import KISAuth
from modules.kis_diagnostic import KISDiagnostic
from modules.kis_trading import KISTrading
from modules.web_server import PortfolioWebServer


def test_portfolio_trading_availability(kis_auth):
    """포트폴리오 종목들의 매매 가능성을 테스트"""
    from modules.kis_portfolio_fetcher import KISPortfolioFetcher
    
    # config_basic.json의 종목들
    test_symbols = {
        "stocks": ["005930", "000660", "035420"],
        "bonds": ["KR103502GA34"]
    }
    
    portfolio_fetcher = KISPortfolioFetcher(kis_auth)
    trading = KISTrading(kis_auth)
    
    print("주식 종목 매매 가능성 테스트:")
    for symbol in test_symbols["stocks"]:
        try:
            # 가격 조회 가능 여부 확인
            price = portfolio_fetcher.fetch_current_price(symbol)
            if price > 0:
                # 테스트 주문 (매우 낮은 가격으로)
                test_order = trading.buy_limit_order(symbol, 1, 1000)
                if "매매불가" in test_order.get("message", ""):
                    print(f"  {symbol}: ❌ 매매불가 종목")
                else:
                    print(f"  {symbol}: ✅ 매매 가능 (가격: {price:,}원)")
            else:
                print(f"  {symbol}: ⚠️ 가격 조회 실패")
        except Exception as e:
            print(f"  {symbol}: ❌ 에러 - {e}")
    
    print("\n채권 종목 매매 가능성 테스트:")
    for symbol in test_symbols["bonds"]:
        try:
            price = portfolio_fetcher.fetch_current_price(symbol)
            if price > 0:
                test_order = trading.buy_limit_order(symbol, 1, int(price * 0.5))
                if "매매불가" in test_order.get("message", ""):
                    print(f"  {symbol}: ❌ 매매불가 종목 (모의투자 미지원)")
                else:
                    print(f"  {symbol}: ✅ 매매 가능 (가격: {price:,}원)")
            else:
                print(f"  {symbol}: ⚠️ 가격 조회 실패")
        except Exception as e:
            print(f"  {symbol}: ❌ 에러 - {e}")


def diagnose_account_access(kis_auth):
    """계좌 접근 관련 상세 진단"""
    from modules.kis_api_utils import execute_api_request_with_retry
    import requests
    
    print(f"계좌 정보: {kis_auth.account}")
    print(f"상품 코드: {kis_auth.product}")
    
    # 1. 토큰 유효성 확인
    print("\n1︎⃣ 토큰 유효성 확인:")
    if kis_auth.access_token:
        print("  ✅ 액세스 토큰 존재")
    else:
        print("  ❌ 액세스 토큰 없음")
        return
    
    # 2. 계좌 잔고 조회 테스트 (원시 API)
    print("\n2︎⃣ 계좌 잔고 조회 테스트:")
    url = f"{kis_auth.base_url}/uapi/domestic-stock/v1/trading/inquire-psbl-order"
    
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "authorization": f"Bearer {kis_auth.access_token}",
        "appkey": kis_auth.appkey,
        "appsecret": kis_auth.appsecret,
        "tr_id": "TTTC8908R",
        "custtype": "P",
        "hashkey": "",
    }
    
    params = {
        "CANO": kis_auth.account,
        "ACNT_PRDT_CD": kis_auth.product,
        "PDNO": "",
        "ORD_UNPR": "",
        "ORD_DVSN": "",
        "CMA_EVLU_AMT_ICLD_YN": "",
        "OVRS_ICLD_YN": ""
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["rt_cd"] == "0":
                print("  ✅ 계좌 잔고 조회 성공")
            else:
                print(f"  ❌ API 응답 에러: {data.get('msg1', 'Unknown error')}")
        else:
            print(f"  ❌ HTTP 에러: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 요청 실패: {e}")
    
    # 3. 보유종목 조회 테스트
    print("\n3︎⃣ 보유종목 조회 테스트:")
    url = f"{kis_auth.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
    
    headers["tr_id"] = "TTTC8434R"
    params = {
        "CANO": kis_auth.account,
        "ACNT_PRDT_CD": kis_auth.product,
        "AFHR_FLPR_YN": "N",
        "OFL_YN": "",
        "INQR_DVSN": "02",
        "UNPR_DVSN": "01",
        "FUND_STTL_ICLD_YN": "N",
        "FNCG_AMT_AUTO_RDPT_YN": "N",
        "PRCS_DVSN": "01",
        "CTX_AREA_FK100": "",
        "CTX_AREA_NK100": ""
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if data["rt_cd"] == "0":
                print("  ✅ 보유종목 조회 성공")
                holdings_count = len(data.get("output1", []))
                print(f"  📊 보유종목 수: {holdings_count}개")
            else:
                print(f"  ❌ API 응답 에러: {data.get('msg1', 'Unknown error')}")
                print(f"  📋 에러 코드: {data.get('msg_cd', 'Unknown')}")
        else:
            print(f"  ❌ HTTP 에러: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 요청 실패: {e}")


def main():
    """메인 진단 함수"""
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    print("🔧 KIS API 진단 도구 시작")
    print("="*60)
    
    try:
        # 1. 설정 파일 로드
        config = get_config()
        
        # 2. KIS 인증 초기화 (모의투자)
        demo_config = config.get_kis_config("demo")
        kis_auth = KISAuth(
            appkey=demo_config["appkey"],
            appsecret=demo_config["appsecret"],
            account=demo_config["account"],
            product=demo_config["product"],
            htsid=demo_config["htsid"],
            env="demo"
        )
        
        print(f"📋 인증 정보:")
        print(f"   환경: {kis_auth.env}")
        print(f"   계좌: {kis_auth.account}")
        print(f"   상품: {kis_auth.product}")
        print(f"   URL: {kis_auth.base_url}")
        print()
        
        # 3. 진단 도구 실행
        diagnostic = KISDiagnostic(kis_auth)
        results = diagnostic.run_full_diagnostic()
        
        # 4. 결과 출력
        print("📊 진단 결과:")
        print("-"*40)
        
        for test_name, result in results["diagnostics"].items():
            status = "✅ 성공" if result["success"] else "❌ 실패"
            print(f"{test_name}: {status}")
            if not result["success"]:
                print(f"   오류: {result['message']}")
        
        print()
        print(f"🎯 전체 상태: {results['overall_status']}")
        
        # 5. 수정된 기능 테스트
        if results["overall_status"] == "정상":
            print()
            print("🔧 수정된 기능 테스트")
            print("-"*40)
            
            # 포트폴리오 조회 모듈 테스트
            from modules.kis_portfolio_fetcher import KISPortfolioFetcher
            portfolio_fetcher = KISPortfolioFetcher(kis_auth)
            
            try:
                print("📋 계정 잔고 조회 테스트...")
                balance = portfolio_fetcher.fetch_account_balance()
                print(f"✅ 계정 잔고 조회 성공: {balance}")
                
                print()
                print("📊 주식 가격 조회 테스트 (삼성전자)...")
                stock_price = portfolio_fetcher.fetch_current_price("005930")
                print(f"✅ 주식 가격: {stock_price:,}원")
                
                print()
                print("💰 채권 가격 조회 테스트 (KR103502GA34)...")
                bond_price = portfolio_fetcher.fetch_current_price("KR103502GA34")
                if bond_price > 0:
                    print(f"✅ 채권 가격: {bond_price:,}원")
                else:
                    print("⚠️ 채권 가격 조회 실패 - 토픽이 없거나 장 마감")
                
                print()
                print("📈 보유종목 조회 테스트...")
                holdings = portfolio_fetcher.fetch_holdings()
                print(f"✅ 보유종목: {holdings}")
                
            except Exception as e:
                print(f"❌ 포트폴리오 기능 테스트 실패: {e}")
        
        # 6. 포트폴리오 종목 매매 가능성 검사
        print()
        print("🔍 포트폴리오 종목 매매 가능성 검사")
        print("-"*40)
        
        test_portfolio_trading_availability(kis_auth)
        
        # 7. 거래 모듈 테스트  
        print()
        print("🚀 거래 모듈 테스트")
        print("-"*40)
        
        trading = KISTrading(kis_auth)
        
        # 매우 낮은 가격의 삼성전자 지정가 매수 주문 (체결되지 않을 것)
        test_result = trading.buy_limit_order(
            stock_code="005930",
            quantity=1,
            price=1000  # 매우 낮은 가격
        )
        
        if test_result["success"]:
            print("✅ 거래 모듈 테스트 성공")
            print(f"   주문번호: {test_result.get('order_no', 'N/A')}")
        else:
            print("❌ 거래 모듈 테스트 실패")
            print(f"   오류: {test_result['message']}")
            
        # 8. 계좌번호 검증 상세 진단
        print()
        print("🔍 계좌번호 상세 진단")
        print("-"*40)
        
        diagnose_account_access(kis_auth)
        
        # 추가 테스트: 웹 서버 테스트
        print()
        print("🌐 웹 서버 테스트")
        print("-"*40)
        test_web_server(kis_auth)
        
    except Exception as e:
        logger.error(f"진단 도구 실행 중 오류: {e}")
        print(f"❌ 진단 도구 실행 실패: {e}")


def test_web_server(kis_auth):
    """웹 서버 기능 테스트"""
    try:
        env = "demo"  # 테스트는 항상 demo로
        
        # 웹 서버 생성 및 테스트
        web_server = PortfolioWebServer(port=5001, host="127.0.0.1", env=env)
        
        # 포트폴리오 데이터 조회 테스트
        portfolio_data = web_server.get_portfolio_data()
        
        if 'error' in portfolio_data:
            print(f"❌ 포트폴리오 데이터 조회 실패: {portfolio_data['error']}")
            return False
        
        print("✅ 포트폴리오 데이터 조회 성공")
        print(f"   총 자산: {portfolio_data['summary']['total_assets']:,.0f}원")
        print(f"   현금: {portfolio_data['summary']['cash']:,.0f}원") 
        print(f"   보유 종목: {len(portfolio_data['positions'])}개")
        
        # 웹 서버 시작 테스트 (짧은 시간)
        print("\n웹 서버 시작 테스트...")
        web_server.start()
        
        import time
        time.sleep(3)  # 3초 대기
        
        if web_server.is_running():
            print("✅ 웹 서버 시작 성공")
            print(f"   URL: http://127.0.0.1:5001")
            print("   (3초 후 자동 종료)")
            
            # 3초 더 대기 후 종료
            time.sleep(3)
            web_server.stop()
            print("✅ 웹 서버 정상 종료")
            return True
        else:
            print("❌ 웹 서버 시작 실패")
            return False
            
    except Exception as e:
        print(f"❌ 웹 서버 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    main()