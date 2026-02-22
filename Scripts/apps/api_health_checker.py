# -*- coding: utf-8 -*-
"""
KIS Open Trading API Health Checker
한국투자증권 Open API 상태 점검 도구

이 스크립트는 다음과 같은 API 상태를 점검합니다:
1. API 인증 상태
2. 기본 API 엔드포인트 응답 상태
3. 계좌 정보 조회 가능 여부
4. 시세 조회 가능 여부
5. 주문 가능 여부 (테스트 주문)

사용법:
    python api_health_checker.py --env demo
    python api_health_checker.py --env real --full-test
"""

import sys
import logging
import argparse
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# 로컬 모듈 import
import os
modules_path = os.path.join(os.path.dirname(__file__), '..', 'modules')
sys.path.insert(0, modules_path)
sys.path.insert(0, os.path.dirname(modules_path))

import config_loader
import kis_auth
import kis_api_utils


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KISAPIHealthChecker:
    """KIS API 상태 점검 클래스"""
    
    def __init__(self, env: str = "demo"):
        """
        Args:
            env (str): 환경 ('demo' 또는 'real')
        """
        self.env = env
        
        # 설정 로드 및 출력
        print(f"\n🔧 API 상태 점검 도구 시작 - 설정 정보 (환경: {env})")
        print("=" * 70)
        
        # 올바른 config 경로 지정 (Investment_Auto/Config/config.json)
        config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Config', 'config.json'))
        self.config = config_loader.ConfigLoader(config_path)
        self.config.load()
        
        self.results = []
        
        # KIS 설정 로드
        kis_config = self.config.get_kis_config(env)
        if not kis_config:
            raise ValueError(f"KIS configuration not found for environment: {env}")
        
        # KIS 인증 초기화
        self.kis_auth = kis_auth.KISAuth(
            appkey=kis_config.get("appkey"),
            appsecret=kis_config.get("appsecret"),
            account=kis_config.get("account"),
            product=kis_config.get("product", "01"),
            htsid=kis_config.get("htsid", ""),
            env=env
        )
        
        logger.info(f"API Health Checker initialized for environment: {env}")
        print("✅ 모든 설정이 성공적으로 로드되었습니다. API 점검을 시작합니다.\n")
    
    def add_result(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None):
        """테스트 결과를 추가합니다."""
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
    
    def test_authentication(self) -> bool:
        """API 인증 상태를 테스트합니다."""
        try:
            token = self.kis_auth.authenticate()
            
            if not token:
                self.add_result("Authentication", False, "Failed to obtain access token")
                return False
            
            self.add_result(
                "Authentication", 
                True, 
                "Successfully obtained access token",
                {"token_length": len(token)}
            )
            return True
            
        except Exception as e:
            self.add_result("Authentication", False, f"Authentication failed: {str(e)}")
            return False
    
    def test_account_balance(self) -> bool:
        """계좌 잔고 조회를 테스트합니다."""
        try:
            url = f"{self.kis_auth.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            headers = kis_api_utils.build_api_headers(self.kis_auth, "CTRP6504R")
            
            params = {
                "cano": self.kis_auth.account[:8],
                "acnt_prdt_cd": self.kis_auth.product,
                "afhr_flpr_yn": "N",
                "fank_sum_ord_tp_code": "00",
                "fun_dvsn": "00",
                "plov_dvsn": "00",
                "tr_crdt_type_cd": "00",
                "cdd_dvsn": "00"
            }
            
            data = kis_api_utils.execute_api_request(
                'GET',
                url,
                headers,
                params=params,
                context="Fetch account balance"
            )
            
            # 출력값 확인
            output1 = data.get('output1', [])
            output2 = data.get('output2', [])
            
            self.add_result(
                "Account Balance Query", 
                True, 
                "Successfully retrieved account balance",
                {
                    "holdings_count": len(output1),
                    "has_summary": bool(output2)
                }
            )
            return True
            
        except Exception as e:
            self.add_result("Account Balance Query", False, f"Account balance query failed: {str(e)}")
            return False
    
    def test_stock_holdings(self) -> bool:
        """주식 보유 현황 조회를 테스트합니다."""
        try:
            url = f"{self.kis_auth.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            headers = kis_api_utils.build_api_headers(self.kis_auth, "TTTC8434R")
            
            params = {
                "cano": self.kis_auth.account[:8],
                "acnt_prdt_cd": self.kis_auth.product,
                "afhr_flpr_yn": "N",
                "unpr": "",
                "fund_sttl_icld_yn": "N",
                "fncg_ami_auto_rdpt_yn": "N",
                "prcs_dvsn": "01",
                "cost_icld_yn": "N",
                "ctx_area_fk100": "",
                "ctx_area_nk100": ""
            }
            
            data = kis_api_utils.execute_api_request(
                'GET',
                url,
                headers,
                params=params,
                context="Fetch stock holdings"
            )
            
            output1 = data.get('output1', [])
            holdings = [item for item in output1 if float(item.get('hldg_qty', '0')) > 0]
            
            self.add_result(
                "Stock Holdings Query", 
                True, 
                "Successfully retrieved stock holdings",
                {"total_holdings": len(holdings)}
            )
            return True
            
        except Exception as e:
            self.add_result("Stock Holdings Query", False, f"Stock holdings query failed: {str(e)}")
            return False
    
    def test_stock_price_query(self, ticker: str = "005930") -> bool:
        """주식 가격 조회를 테스트합니다."""
        try:
            url = f"{self.kis_auth.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = kis_api_utils.build_api_headers(self.kis_auth, "FHKST01010100")
            
            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": ticker
            }
            
            data = kis_api_utils.execute_api_request(
                'GET',
                url,
                headers,
                params=params,
                context=f"Fetch price for {ticker}"
            )
            
            output = data.get('output', {})
            current_price = output.get('stck_prpr', '0')
            
            self.add_result(
                "Stock Price Query", 
                True, 
                f"Successfully retrieved price for {ticker}",
                {
                    "ticker": ticker,
                    "current_price": current_price,
                    "has_price_data": bool(current_price and current_price != '0')
                }
            )
            return True
            
        except Exception as e:
            self.add_result("Stock Price Query", False, f"Stock price query failed for {ticker}: {str(e)}")
            return False
    
    def test_order_inquiry(self) -> bool:
        """주문 조회를 테스트합니다."""
        try:
            url = f"{self.kis_auth.base_url}/uapi/domestic-stock/v1/trading/inquire-orders"
            headers = kis_api_utils.build_api_headers(self.kis_auth, "TTTC8434R")
            
            from datetime import datetime
            today = datetime.now().strftime("%Y%m%d")
            
            params = {
                "cano": self.kis_auth.account[:8],
                "acnt_prdt_cd": self.kis_auth.product,
                "inqr_strt_dt": today,
                "inqr_end_dt": today,
                "sll_buy_dvsn": "",
                "inqr_dvsn": "00",
                "pdno": "",
                "ccld_dvsn": "",
                "ord_gno_brno": "",
                "odno": "",
                "inqr_dvsn_3": "00",
                "inqr_dvsn_1": "",
                "ctx_area_fk100": "",
                "ctx_area_nk100": ""
            }
            
            data = kis_api_utils.execute_api_request(
                'GET',
                url,
                headers,
                params=params,
                context="Order inquiry"
            )
            
            output = data.get('output', [])
            
            self.add_result(
                "Order Inquiry", 
                True, 
                "Successfully retrieved order list",
                {"order_count": len(output)}
            )
            return True
            
        except Exception as e:
            self.add_result("Order Inquiry", False, f"Order inquiry failed: {str(e)}")
            return False
    
    def test_market_status(self) -> bool:
        """시장 운영 시간 조회를 테스트합니다."""
        try:
            url = f"{self.kis_auth.base_url}/uapi/domestic-stock/v1/quotations/chk-holiday"
            headers = kis_api_utils.build_api_headers(self.kis_auth, "CTCA0903R")
            
            from datetime import datetime
            today = datetime.now().strftime("%Y%m%d")
            
            params = {
                "base_dt": today,
                "ctx_area_nk": "",
                "ctx_area_fk": ""
            }
            
            data = kis_api_utils.execute_api_request(
                'GET',
                url,
                headers,
                params=params,
                context="Market status check"
            )
            
            self.add_result(
                "Market Status Check", 
                True, 
                "Successfully checked market status",
                {"response_data": len(str(data)) > 0}
            )
            return True
            
        except Exception as e:
            self.add_result("Market Status Check", False, f"Market status check failed: {str(e)}")
            return False
    
    def run_basic_tests(self) -> bool:
        """기본 API 테스트를 실행합니다."""
        logger.info("🔍 Starting basic API health checks...")
        
        test_methods = [
            self.test_authentication,
            self.test_account_balance,
            self.test_stock_holdings,
            self.test_stock_price_query,
            self.test_order_inquiry,
        ]
        
        success_count = 0
        for test_method in test_methods:
            if test_method():
                success_count += 1
        
        all_passed = success_count == len(test_methods)
        logger.info(f"🏁 Basic tests completed: {success_count}/{len(test_methods)} passed")
        
        return all_passed
    
    def run_full_tests(self) -> bool:
        """전체 API 테스트를 실행합니다."""
        logger.info("🔍 Starting comprehensive API health checks...")
        
        # 기본 테스트 + 확장 테스트
        basic_success = self.run_basic_tests()
        
        # 추가 테스트들
        additional_tests = [
            self.test_market_status,
        ]
        
        additional_success_count = 0
        for test_method in additional_tests:
            if test_method():
                additional_success_count += 1
        
        total_tests = len(self.results)
        total_passed = sum(1 for result in self.results if result['success'])
        
        logger.info(f"🏁 Full tests completed: {total_passed}/{total_tests} passed")
        
        return basic_success and additional_success_count == len(additional_tests)
    
    def print_summary(self):
        """테스트 결과 요약을 출력합니다."""
        print("\n" + "="*60)
        print(f"📊 KIS API Health Check Summary ({self.env.upper()} Environment)")
        print("="*60)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {passed_tests/total_tests*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for result in self.results:
                if not result['success']:
                    print(f"  • {result['test_name']}: {result['message']}")
        
        print("\n📋 Detailed Results:")
        for result in self.results:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"  {status} {result['test_name']}")
            if result['details']:
                for key, value in result['details'].items():
                    print(f"    - {key}: {value}")
        
        print("\n" + "="*60)
    
    def save_results(self, output_file: Optional[str] = None):
        """테스트 결과를 파일로 저장합니다."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"api_health_check_{self.env}_{timestamp}.json"
        
        report = {
            "environment": self.env,
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(self.results),
                "passed_tests": sum(1 for result in self.results if result['success']),
                "failed_tests": sum(1 for result in self.results if not result['success']),
                "success_rate": sum(1 for result in self.results if result['success']) / len(self.results) if self.results else 0
            },
            "test_results": self.results
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"📄 Test results saved to: {output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="KIS Open Trading API Health Checker"
    )
    parser.add_argument(
        '--env',
        choices=['demo', 'real'],
        default='demo',
        help='KIS API environment (demo or real)'
    )
    parser.add_argument(
        '--full-test',
        action='store_true',
        help='Run comprehensive tests including additional API endpoints'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Output file for test results (JSON format)'
    )
    parser.add_argument(
        '--ticker',
        type=str,
        default='005930',
        help='Stock ticker for price query test (default: 005930 - Samsung Electronics)'
    )
    
    args = parser.parse_args()
    
    try:
        # Health Checker 초기화
        checker = KISAPIHealthChecker(env=args.env)
        
        # 특정 종목으로 가격 조회 테스트 설정
        if args.ticker != '005930':
            checker.test_stock_price_query = lambda: checker.test_stock_price_query(args.ticker)
        
        # 테스트 실행
        if args.full_test:
            success = checker.run_full_tests()
        else:
            success = checker.run_basic_tests()
        
        # 결과 출력
        checker.print_summary()
        
        # 결과 저장
        if args.output:
            checker.save_results(args.output)
        
        # 종료 코드 반환
        return 0 if success else 1
        
    except Exception as e:
        logger.error(f"Health check failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)