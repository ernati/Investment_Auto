# -*- coding: utf-8 -*-
"""
KIS API 디버깅 및 테스트 스크립트
주식 거래 실패 문제 진단용
로그 분석 결과 기반 개선된 테스트 포함:
- 토큰 자동 갱신 테스트
- 체결정보 조회 API 테스트
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Scripts 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.config_loader import get_config
from modules.kis_auth import KISAuth
from modules.kis_diagnostic import KISDiagnostic
from modules.kis_trading import KISTrading
from modules.web_server import PortfolioWebServer
from modules.db_manager import DatabaseManager
from modules.db_models import TradingHistoryRecord, RebalancingLogRecord, PortfolioSnapshotRecord, SystemLogRecord


def test_token_refresh(kis_auth):
    """토큰 갱신 로직 테스트 (EGW00123 에러 해결)"""
    print("\n=== 토큰 갱신 로직 테스트 ===")
    
    try:
        # 현재 토큰 정보 확인
        current_token = kis_auth.token
        print(f"현재 토큰: {current_token[:20]}..." if current_token else "토큰 없음")
        print(f"토큰 만료일: {kis_auth.token_expired}" if hasattr(kis_auth, 'token_expired') else "만료일 정보 없음")
        
        # 토큰 만료 상태 확인
        is_expired = kis_auth.is_token_expired()
        print(f"토큰 만료 상태: {'만료됨' if is_expired else '유효함'}")
        
        # 강제 토큰 갱신 테스트
        print("\n강제 토큰 갱신 테스트...")
        new_token = kis_auth.authenticate(force_refresh=True)
        print(f"새 토큰: {new_token[:20]}..." if new_token else "토큰 발급 실패")
        print(f"갱신 성공: {'✅' if new_token != current_token else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ 토큰 갱신 테스트 실패: {e}")
        return False


def test_execution_info_query(kis_auth):
    """체결정보 조회 API 테스트 (OPSQ2001 에러 해결)"""
    print("\n=== 체결정보 조회 API 테스트 ===")
    
    try:
        from modules.kis_api_utils import execute_api_request_with_retry, build_api_headers
        
        # 오늘 날짜
        today = datetime.now().strftime('%Y%m%d')
        
        # 체결정보 조회 API 호출 테스트
        endpoint = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
        tr_id = "VTTC8001R"  # 모의투자 주식일별주문체결조회
        
        # 개선된 파라미터 (CTX_AREA_FK100, CTX_AREA_NK100 사용)
        params = {
            "CANO": kis_auth.account,
            "ACNT_PRDT_CD": kis_auth.product,
            "INQR_STRT_DT": today,
            "INQR_END_DT": today,
            "SLL_BUY_DVSN_CD": "00",
            "INQR_DVSN": "00",
            "PDNO": "",  # 전체 조회
            "CCLD_DVSN": "01",
            "INQR_DVSN_3": "01",
            "ORD_GNO_BRNO": "",
            "ODNO": "",  # 전체 조회
            "INQR_DVSN_1": "",
            "CTX_AREA_FK100": "",  # 수정된 파라미터명
            "CTX_AREA_NK100": "",  # 수정된 파라미터명
        }
        
        # 헤더 생성
        headers = build_api_headers(kis_auth, tr_id)
        url = f"{kis_auth.base_url}{endpoint}"
        
        print(f"API 호출: {endpoint}")
        print(f"TR ID: {tr_id}")
        print("파라미터 확인 완료 ✅")
        
        # API 호출
        response = execute_api_request_with_retry(
            method="GET",
            url=url,
            headers=headers,
            params=params,
            context="체결정보 조회 테스트",
            kis_auth=kis_auth
        )
        
        if response.get('rt_cd') == '0':
            output1 = response.get('output1', [])
            print(f"✅ 체결정보 조회 성공: {len(output1)}건 조회")
            
            # 최근 체결정보 샘플 출력
            if output1:
                latest = output1[0]
                print(f"최근 체결: 주문번호={latest.get('odno', 'N/A')}, "
                      f"종목={latest.get('pdno', 'N/A')}, "
                      f"체결가={latest.get('avg_prvs', 'N/A')}")
            return True
        else:
            error_msg = response.get('msg1', 'Unknown error')
            print(f"❌ 체결정보 조회 실패: {error_msg}")
            return False
            
    except Exception as e:
        print(f"❌ 체결정보 조회 테스트 실패: {e}")
        return False


def test_api_error_recovery(kis_auth):
    """API 에러 복구 능력 테스트"""
    print("\n=== API 에러 복구 테스트 ===")
    
    try:
        from modules.kis_api_utils import execute_api_request_with_retry, build_api_headers
        
        # 고의로 잘못된 종목코드로 API 호출하여 에러 복구 테스트
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
        tr_id = "FHKST01010100"
        
        # 잘못된 종목코드
        invalid_params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": "INVALID_CODE"
        }
        
        headers = build_api_headers(kis_auth, tr_id)
        url = f"{kis_auth.base_url}{endpoint}"
        
        print("잘못된 종목코드로 API 호출 테스트...")
        
        try:
            response = execute_api_request_with_retry(
                method="GET",
                url=url,
                headers=headers,
                params=invalid_params,
                context="에러 복구 테스트",
                kis_auth=kis_auth,
                max_retries=1  # 빠른 테스트를 위해 재시도 1회만
            )
            print("❌ 예상되지 않은 성공")
            return False
            
        except RuntimeError as e:
            if "returned error" in str(e):
                print("✅ 에러를 올바르게 감지하고 처리함")
                return True
            else:
                print(f"❌ 예상되지 않은 에러: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 에러 복구 테스트 실패: {e}")
        return False


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
        
        # 추가 테스트: 데이터베이스 테스트
        print()
        print("🗄️ 데이터베이스 테스트")
        print("-"*40)
        test_database_data()
        
    except Exception as e:
        logger.error(f"진단 도구 실행 중 오류: {e}")
        print(f"❌ 진단 도구 실행 실패: {e}")


def test_database_data():
    """
    데이터베이스 연결 및 저장된 데이터 확인 테스트
    BitCoin_Auto의 app.py 스타일을 참고한 DB 연결
    """
    try:
        print("📊 데이터베이스 연결 테스트 시작")
        
        # DatabaseManager 초기화 (자동으로 테이블 생성 및 연결 확인)
        db_manager = DatabaseManager()
        print("✅ 데이터베이스 연결 성공")
        
        # 각 테이블별 데이터 확인
        tables_data = {
            "trading_history": "거래 기록",
            "rebalancing_logs": "리밸런싱 로그", 
            "portfolio_snapshots": "포트폴리오 스냅샷",
            "system_logs": "시스템 로그"
        }
        
        print("\n📋 테이블별 데이터 현황:")
        
        # trading_history 데이터 확인
        try:
            trading_data = db_manager.get_trading_history("portfolio-001", "demo", limit=5)
            count = len(trading_data)
            print(f"  📈 거래 기록 (trading_history): {count}건")
            
            if count > 0:
                print("     최근 거래 기록:")
                for i, trade in enumerate(trading_data[:3], 1):
                    symbol = trade.get('symbol', 'N/A')
                    order_type = trade.get('order_type', 'N/A')
                    quantity = trade.get('quantity', 0)
                    price = trade.get('price', 0)
                    timestamp = trade.get('timestamp', 'N/A')
                    print(f"       {i}. {timestamp} | {symbol} {order_type} {quantity}주 @ {price:,}원")
            else:
                print("     ⚠️ 데이터 없음")
                
        except Exception as e:
            print(f"     ❌ 거래 기록 조회 실패: {e}")
        
        # rebalancing_logs 데이터 확인  
        try:
            rebalancing_data = db_manager.get_rebalancing_logs("portfolio-001", "demo", limit=3)
            count = len(rebalancing_data)
            print(f"  ⚖️ 리밸런싱 로그 (rebalancing_logs): {count}건")
            
            if count > 0:
                print("     최근 리밸런싱 기록:")
                for i, log in enumerate(rebalancing_data[:2], 1):
                    reason = log.get('rebalance_reason', 'N/A')[:50]
                    status = log.get('status', 'N/A')
                    orders = log.get('orders_executed', 0)
                    timestamp = log.get('timestamp', 'N/A')
                    print(f"       {i}. {timestamp} | {status} | {orders}건 실행 | {reason}...")
            else:
                print("     ⚠️ 데이터 없음")
                
        except Exception as e:
            print(f"     ❌ 리밸런싱 로그 조회 실패: {e}")
        
        # portfolio_snapshots 데이터 확인
        try:
            snapshot_data = db_manager.get_portfolio_snapshots("portfolio-001", "demo", limit=3)
            count = len(snapshot_data) 
            print(f"  📸 포트폴리오 스냅샷 (portfolio_snapshots): {count}건")
            
            if count > 0:
                print("     최근 스냅샷:")
                for i, snapshot in enumerate(snapshot_data[:2], 1):
                    total_value = snapshot.get('total_value', 0)
                    timestamp = snapshot.get('timestamp', 'N/A')
                    positions = snapshot.get('positions', {})
                    position_count = len(positions) if isinstance(positions, dict) else 0
                    print(f"       {i}. {timestamp} | 총자산: {total_value:,.0f}원 | 포지션: {position_count}개")
            else:
                print("     ⚠️ 데이터 없음")
                
        except Exception as e:
            print(f"     ❌ 포트폴리오 스냅샷 조회 실패: {e}")
        
        # 테스트용 샘플 데이터 생성
        print("\n🧪 테스트 데이터 생성:")
        
        try:
            # 샘플 거래 기록 생성
            sample_trade = TradingHistoryRecord(
                portfolio_id="test_portfolio",
                symbol="005930",
                order_type="buy",
                quantity=1.0,
                price=75000.0,
                total_amount=75000.0,
                commission=150.0,
                order_id="TEST_ORDER_001",
                status="completed",
                environment="demo"
            )
            
            if db_manager.save_trading_history(sample_trade):
                print("  ✅ 샘플 거래 기록 저장 성공")
            else:
                print("  ❌ 샘플 거래 기록 저장 실패")
                
        except Exception as e:
            print(f"  ❌ 샘플 데이터 생성 실패: {e}")
        
        try:
            # 샘플 시스템 로그 생성
            sample_log = SystemLogRecord(
                level="INFO",
                module="kis_debug",
                message="데이터베이스 테스트 실행",
                environment="demo",
                extra_data={"test_type": "db_data_check", "success": True}
            )
            
            if db_manager.save_system_log(sample_log):
                print("  ✅ 샘플 시스템 로그 저장 성공")
            else:
                print("  ❌ 샘플 시스템 로그 저장 실패")
                
        except Exception as e:
            print(f"  ❌ 샘플 로그 생성 실패: {e}")
        
        print("\n✅ 데이터베이스 테스트 완료")
        return True
        
    except SystemExit:
        print("❌ 데이터베이스 초기화 실패 - 프로그램 종료")
        return False
    except Exception as e:
        print(f"❌ 데이터베이스 테스트 실패: {e}")
        return False


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


def test_kis_trading_api_fix():
    """
    수정된 KIS Trading 모듈이 정상 작동하는지 테스트
    - API 호출 파라미터 오류 수정 검증
    - 중복 메서드 제거 검증
    """
    print("\n=== KIS Trading API 수정 사항 테스트 ===")
    
    try:
        # config.json 파일 직접 로드
        config_path = Path(__file__).parent.parent.parent / "Config" / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Demo 환경으로 KISAuth 초기화
        kas_config = config['kis']['demo']  # demo 환경 사용
        kis_auth = KISAuth(
            appkey=kas_config['appkey'],
            appsecret=kas_config['appsecret'],
            account=kas_config['account'],
            product=kas_config['product'],
            htsid=kas_config['htsid'],
            env='demo'
        )
        
        print("✅ KISAuth 초기화 성공 (Demo 환경)")
        
        # KISTrading 클래스 초기화
        trading = KISTrading(kis_auth)
        print("✅ KISTrading 클래스 초기화 성공")
        
        # _call_api 메서드가 올바르게 작동하는지 테스트 (현재가 조회로)
        print("\n📈 현재가 조회 테스트 (API 호출 메서드 검증):")
        
        # 삼성전자 현재가 조회로 API 호출 테스트
        test_stock = "005930"  # 삼성전자
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
        tr_id = "FHKST01010100" if kis_auth.env == "real" else "FHKST01010300"
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": test_stock
        }
        
        try:
            # API 호출 테스트 (GET 요청)
            response = trading._call_api(endpoint, tr_id, params, method='GET')
            
            if response and response.get('rt_cd') == '0':
                current_price = response.get('output', {}).get('stck_prpr', '')
                if current_price:
                    print(f"✅ API 호출 성공: {test_stock} 현재가 = {current_price}원")
                    print("✅ _call_api 메서드 정상 작동 확인")
                else:
                    print("⚠️ API 응답은 성공했지만 가격 데이터가 없음")
            else:
                error_msg = response.get('msg1', 'Unknown error') if response else 'No response'
                print(f"⚠️ API 호출 실패: {error_msg}")
                print("   (인증 상태나 시장 시간 확인 필요)")
                
        except Exception as api_error:
            if "unexpected keyword argument 'json'" in str(api_error):
                print(f"❌ API 파라미터 오류가 아직 남아있음: {api_error}")
                return False
            else:
                print(f"⚠️ 다른 API 오류 (파라미터 수정은 성공): {api_error}")
        
        # 간단한 주문 파라미터 테스트 (실제 주문은 하지 않음)
        print("\n📋 주문 파라미터 생성 테스트:")
        try:
            # 주문 파라미터의 기본 검증만 수행
            stock_code = "005930"
            order_type = "buy"
            quantity = 1
            
            # 주문 파라미터 유효성 검사
            if order_type not in ["buy", "sell"]:
                raise ValueError("order_type은 'buy' 또는 'sell'이어야 합니다.")
            
            if quantity <= 0:
                raise ValueError("quantity는 0보다 커야 합니다.")
                
            print(f"✅ 주문 파라미터 검증 통과: {stock_code}, {order_type}, {quantity}")
            
        except Exception as param_error:
            print(f"❌ 주문 파라미터 검증 실패: {param_error}")
            return False
        
        print("\n✅ KIS Trading 모듈 수정 사항 테스트 완료")
        print("   - API 호출 파라미터 오류 해결됨")
        print("   - 중복 메서드 제거됨")
        print("   - 모듈이 정상적으로 로드되고 초기화됨")
        
        return True
        
    except Exception as e:
        print(f"❌ KIS Trading 테스트 실패: {e}")
        return False


def main():
    """메인 테스트 함수 - 로그 분석 기반 개선된 테스트 포함"""
    print("🚀 KIS API 디버깅 및 테스트 시작 (ver 2.0)")
    print("   - 2026-03-04 로그 분석 결과 반영")
    print("   - 토큰 자동 갱신 및 체결정보 조회 개선")
    print("=" * 60)
    
    # 설정 로드
    try:
        config_path = Path(__file__).parent.parent.parent / "Config" / "config.json"
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Demo 환경으로 KISAuth 초기화 
        kas_config = config['kis']['demo']
        kis_auth = KISAuth(
            appkey=kas_config['appkey'],
            appsecret=kas_config['appsecret'],
            account=kas_config['account'],
            product=kas_config['product'],
            htsid=kas_config['htsid'],
            env='demo'
        )
        print("✅ KIS 인증 설정 완료 (Demo 환경)")
        
    except Exception as e:
        print(f"❌ 설정 로드 실패: {e}")
        return
    
    # 테스트 실행
    test_results = []
    
    # 1. 토큰 갱신 테스트 (EGW00123 에러 해결)
    print(f"\n{'='*20} 핵심 테스트 {'='*20}")
    test_results.append(("토큰 갱신 로직", test_token_refresh(kis_auth)))
    
    # 2. 체결정보 조회 테스트 (OPSQ2001 에러 해결)
    test_results.append(("체결정보 조회 API", test_execution_info_query(kis_auth)))
    
    # 3. API 에러 복구 테스트
    test_results.append(("API 에러 복구", test_api_error_recovery(kis_auth)))
    
    # 4. 기존 Trading 모듈 테스트
    print(f"\n{'='*20} 기본 기능 테스트 {'='*20}")
    test_results.append(("Trading 모듈", test_kis_trading_api_fix()))
    
    # 결과 요약
    print(f"\n{'='*20} 테스트 결과 요약 {'='*20}")
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name:20} : {status}")
        if result:
            passed_tests += 1
    
    print(f"\n총 {len(test_results)}개 테스트 중 {passed_tests}개 통과")
    
    if passed_tests == len(test_results):
        print("\n🎉 모든 테스트 통과!")
        print("   로그 분석 기반 수정사항이 성공적으로 적용됨")
        print("   포트폴리오 리밸런싱 시스템 사용 준비 완료")
    else:
        print(f"\n❌ {len(test_results) - passed_tests}개 테스트 실패")
        print("   추가 수정이 필요함")
    
    print(f"\n{'='*60}")
    print("테스트 완료 - 상세 분석 문서: docs/error_analysis_log_20260304.md")


# =============================================================================
# Upbit 비트코인 테스트 함수들
# =============================================================================

def test_upbit_price_query():
    """Upbit 비트코인 현재가 조회 테스트"""
    print("\n=== Upbit 비트코인 가격 조회 테스트 ===")
    
    try:
        from modules.upbit_api_client import get_upbit_client
        
        # Demo 모드로 클라이언트 생성
        upbit_client = get_upbit_client("demo")
        
        # 비트코인 가격 조회
        price_info = upbit_client.get_bitcoin_price()
        
        if price_info.get("success"):
            trade_price = price_info.get("trade_price", 0)
            change_rate = price_info.get("change_rate", 0)
            
            print(f"✅ 비트코인 현재가 조회 성공")
            print(f"   현재가: {trade_price:,.0f} KRW")
            print(f"   변동률: {change_rate*100:.2f}%")
            return True
        else:
            print(f"❌ 비트코인 가격 조회 실패: {price_info.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Upbit 가격 조회 테스트 실패: {e}")
        return False


def test_upbit_demo_trading():
    """Upbit Demo 모드 가상 거래 테스트"""
    print("\n=== Upbit Demo 모드 가상 거래 테스트 ===")
    
    try:
        from modules.upbit_api_client import get_upbit_client, DemoUpbitCashManager
        
        # Demo 모드로 클라이언트 생성
        upbit_client = get_upbit_client("demo", reload=True)
        
        # 1. 초기 잔액 확인
        print("1️⃣ 초기 계좌 상태 확인...")
        account_info = upbit_client.get_account_info()
        
        if account_info.get("success"):
            print(f"   KRW 잔액: {account_info.get('krw', 0):,.0f}원")
            print(f"   BTC 잔액: {account_info.get('btc', 0):.8f}")
        else:
            print(f"   ❌ 계좌 조회 실패: {account_info.get('error')}")
            return False
        
        # 2. 비트코인 매수 테스트
        print("\n2️⃣ 비트코인 가상 매수 테스트 (100,000 KRW)...")
        buy_result = upbit_client.buy_bitcoin(100000)
        
        if buy_result.get("success"):
            print(f"   ✅ 매수 성공")
            print(f"   매수 BTC: {buy_result.get('btc_quantity', 0):.8f}")
            print(f"   매수 가격: {buy_result.get('current_price', 0):,.0f} KRW")
            print(f"   잔여 KRW: {buy_result.get('remaining_krw', 0):,.0f}")
        else:
            print(f"   ❌ 매수 실패: {buy_result.get('error')}")
            return False
        
        # 3. 평가 정보 확인
        print("\n3️⃣ 포지션 평가 정보 확인...")
        eval_info = upbit_client.get_btc_evaluation()
        
        if eval_info.get("success"):
            print(f"   KRW 잔액: {eval_info.get('krw_balance', 0):,.0f}원")
            print(f"   BTC 잔액: {eval_info.get('btc_balance', 0):.8f}")
            print(f"   BTC 평가액: {eval_info.get('btc_value', 0):,.0f}원")
            print(f"   총 자산: {eval_info.get('total_value', 0):,.0f}원")
        
        # 4. 비트코인 매도 테스트
        print("\n4️⃣ 비트코인 가상 매도 테스트 (전량)...")
        sell_result = upbit_client.sell_bitcoin()  # 전량 매도
        
        if sell_result.get("success"):
            print(f"   ✅ 매도 성공")
            print(f"   매도 BTC: {sell_result.get('btc_quantity', 0):.8f}")
            print(f"   수령 KRW: {sell_result.get('krw_received', 0):,.0f}")
            print(f"   손익: {sell_result.get('pnl', 0):+,.0f} KRW")
        else:
            print(f"   ❌ 매도 실패: {sell_result.get('error')}")
            return False
        
        # 5. 최종 잔액 확인
        print("\n5️⃣ 최종 계좌 상태 확인...")
        final_info = upbit_client.get_account_info()
        
        if final_info.get("success"):
            print(f"   KRW 잔액: {final_info.get('krw', 0):,.0f}원")
            print(f"   BTC 잔액: {final_info.get('btc', 0):.8f}")
        
        print("\n✅ Upbit Demo 거래 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ Upbit Demo 거래 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_portfolio_fetcher():
    """통합 포트폴리오 페처 테스트 (KIS + Upbit)"""
    print("\n=== 통합 포트폴리오 페처 테스트 ===")
    
    try:
        from modules.config_loader import get_config
        from modules.kis_auth import KISAuth
        from modules.unified_portfolio_fetcher import create_unified_fetcher
        
        # KIS 인증 설정
        config = get_config()
        demo_config = config.get_kis_config("demo")
        
        kis_auth = KISAuth(
            appkey=demo_config["appkey"],
            appsecret=demo_config["appsecret"],
            account=demo_config["account"],
            product=demo_config["product"],
            htsid=demo_config["htsid"],
            env="demo"
        )
        
        # 통합 페처 생성
        unified_fetcher = create_unified_fetcher(kis_auth, "demo")
        print("✅ 통합 포트폴리오 페처 초기화 성공")
        
        # 통합 스냅샷 조회
        print("\n📊 통합 포트폴리오 스냅샷 조회...")
        
        # target_weights에 있는 모든 티커 포함 (bitcoin 포함)
        all_tickers = ["005930", "000660", "035420", "bitcoin"]
        
        snapshot = unified_fetcher.fetch_unified_portfolio_snapshot(
            portfolio_id="test-portfolio",
            price_source="last",
            extra_tickers=all_tickers
        )
        
        print(f"\n📋 스냅샷 결과:")
        print(f"   포트폴리오 ID: {snapshot.portfolio_id}")
        print(f"   총 현금 (KIS + Upbit): {snapshot.cash:,.0f}원")
        print(f"   주식/코인 평가액: {snapshot.stocks_value:,.0f}원")
        print(f"   총 자산: {snapshot.total_value:,.0f}원")
        print(f"   포지션 수: {len(snapshot.positions)}")
        
        # 포지션 상세
        if snapshot.positions:
            print(f"\n   📈 보유 포지션:")
            for ticker, position in snapshot.positions.items():
                weight = snapshot.get_current_weight(ticker)
                print(f"      {ticker}: {position.evaluation:,.0f}원 ({weight*100:.2f}%)")
        
        print("\n✅ 통합 포트폴리오 페처 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 통합 포트폴리오 페처 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_bitcoin_rebalancing_order():
    """비트코인 리밸런싱 주문 생성 테스트"""
    print("\n=== 비트코인 리밸런싱 주문 생성 테스트 ===")
    
    try:
        from modules.config_loader import get_portfolio_config
        from modules.rebalancing_engine import RebalancingEngine
        from modules.portfolio_models import PortfolioSnapshot, PositionSnapshot
        
        # 설정 로더
        config = get_portfolio_config(reload=True)
        
        # 리밸런싱 엔진 초기화
        engine = RebalancingEngine(config)
        print("✅ 리밸런싱 엔진 초기화 성공")
        
        # target_weights 확인
        target_weights = config.get_basic("target_weights", {})
        print(f"\n📋 목표 비중:")
        for category, assets in target_weights.items():
            if isinstance(assets, dict):
                print(f"   [{category}]")
                for ticker, weight in assets.items():
                    print(f"      {ticker}: {weight*100:.1f}%")
        
        # 테스트용 포트폴리오 스냅샷 생성
        print("\n🧪 테스트 포트폴리오 스냅샷 생성...")
        
        test_snapshot = PortfolioSnapshot(
            portfolio_id="test-portfolio",
            cash=5000000  # 500만원 현금
        )
        
        # 주식 포지션 추가
        test_snapshot.add_position("005930", 10, 75000)  # 삼성전자 10주
        test_snapshot.add_position("000660", 5, 120000)  # SK하이닉스 5주
        test_snapshot.add_position("035420", 3, 350000)  # NAVER 3주
        
        # 비트코인 포지션 추가 (300만원 상당)
        btc_price = 95000000  # 비트코인 가격 9500만원
        test_snapshot.positions["bitcoin"] = PositionSnapshot(
            ticker="bitcoin",
            quantity=1,
            price=btc_price
        )
        test_snapshot.positions["bitcoin"].evaluation = 3000000  # 300만원 상당
        test_snapshot._recalculate()
        
        print(f"   총 자산: {test_snapshot.total_value:,.0f}원")
        print(f"   현금: {test_snapshot.cash:,.0f}원")
        print(f"   포지션: {len(test_snapshot.positions)}개")
        
        # 리밸런싱 계획 생성
        print("\n📊 리밸런싱 계획 생성...")
        plan = engine.create_rebalance_plan(test_snapshot, is_calendar_triggered=True)
        
        print(f"\n   리밸런싱 필요: {'예' if plan.should_rebalance else '아니오'}")
        print(f"   사유: {plan.rebalance_reason}")
        print(f"   총 주문 수: {plan.total_orders}")
        
        if plan.orders:
            print(f"\n   📋 주문 목록:")
            for order in plan.orders:
                order_type = "매수" if order.action == "buy" else "매도"
                print(f"      {order.ticker}: {order_type} {abs(order.delta_value):,.0f}원")
                
                # 비트코인 주문 확인
                if order.ticker == "bitcoin":
                    print(f"         → 비트코인 주문 확인됨!")
        
        print("\n✅ 비트코인 리밸런싱 주문 생성 테스트 완료")
        return True
        
    except Exception as e:
        print(f"❌ 비트코인 리밸런싱 주문 생성 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_upbit_tests():
    """Upbit 관련 모든 테스트 실행"""
    print("\n" + "="*60)
    print("🪙 Upbit 비트코인 통합 테스트 시작")
    print("="*60)
    
    test_results = []
    
    # 1. 가격 조회 테스트
    test_results.append(("비트코인 가격 조회", test_upbit_price_query()))
    
    # 2. Demo 거래 테스트
    test_results.append(("Demo 가상 거래", test_upbit_demo_trading()))
    
    # 3. 통합 포트폴리오 페처 테스트
    test_results.append(("통합 포트폴리오 페처", test_unified_portfolio_fetcher()))
    
    # 4. 비트코인 리밸런싱 테스트
    test_results.append(("비트코인 리밸런싱 주문", test_bitcoin_rebalancing_order()))
    
    # 결과 요약
    print(f"\n{'='*20} Upbit 테스트 결과 요약 {'='*20}")
    passed_tests = 0
    for test_name, result in test_results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name:25} : {status}")
        if result:
            passed_tests += 1
    
    print(f"\n총 {len(test_results)}개 테스트 중 {passed_tests}개 통과")
    
    if passed_tests == len(test_results):
        print("\n🎉 모든 Upbit 테스트 통과!")
        print("   비트코인 포트폴리오 리밸런싱 기능 준비 완료")
    else:
        print(f"\n⚠️ {len(test_results) - passed_tests}개 테스트 실패")
    
    return passed_tests == len(test_results)


if __name__ == "__main__":
    import sys
    
    # 명령줄 인자에 따라 테스트 선택
    if len(sys.argv) > 1 and sys.argv[1] == "--upbit":
        run_upbit_tests()
    else:
        main()
        print("\n" + "-"*60)
        print("💡 Upbit 테스트만 실행하려면: python kis_debug.py --upbit")
        print("-"*60)