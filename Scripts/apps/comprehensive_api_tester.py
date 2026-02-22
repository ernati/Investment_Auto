# -*- coding: utf-8 -*-
"""
Comprehensive KIS API Tester
한국투자증권 API 포괄적 상태 점검 도구

모든 주요 API 엔드포인트를 체계적으로 테스트하여
정확한 문제점과 원인을 파악합니다.
"""

import sys
import json
import logging
import requests
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple

# 로컬 모듈 경로 추가
modules_path = os.path.join(os.path.dirname(__file__), '..', 'modules')
sys.path.insert(0, modules_path)

import config_loader

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveKISAPITester:
    """포괄적 KIS API 테스트 클래스"""
    
    def __init__(self, env: str = "demo"):
        """
        Args:
            env (str): 환경 ('demo' 또는 'real')
        """
        self.env = env
        self.results = []
        self.access_token = None
        self.test_count = 0
        self.success_count = 0
        
        # 설정 파일 로드
        self._load_config()
        
        # API URL 설정
        if env == 'real':
            self.base_url = "https://openapi.koreainvestment.com:9443"
        else:
            self.base_url = "https://openapivts.koreainvestment.com:29443"
        
        # 테스트 종목들
        self.test_tickers = [
            "005930",  # 삼성전자
            "000660",  # SK하이닉스  
            "035420",  # NAVER
            "005380",  # 현대차
            "068270",  # 셀트리온
            "035720",  # 카카오
            "207940",  # 삼성바이오로직스
            "006400",  # 삼성SDI
            "051910",  # LG화학
            "012330"   # 현대모비스
        ]
        
        logger.info(f"Comprehensive KIS API Tester initialized for {env} environment")
        print("✅ 모든 설정이 성공적으로 로드되었습니다. 포괄적 API 테스트를 시작합니다.\n")
    
    def _load_config(self):
        """설정 파일 로드 및 출력"""
        try:
            # 설정 로드 및 출력
            print(f"\n🔧 포괄적 API 테스터 시작 - 설정 정보 (환경: {self.env})")
            print("=" * 80)
            
            config = config_loader.get_config()
            config.load()
            config.print_loaded_config()
            
            kis_config = config.get_kis_config(self.env)
            if not kis_config:
                raise ValueError(f"Configuration not found for environment: {self.env}")
            
            self.appkey = kis_config.get("appkey")
            self.appsecret = kis_config.get("appsecret")
            self.account = kis_config.get("account")
            self.product = kis_config.get("product", "01")
            self.htsid = kis_config.get("htsid", "")
            
            if not all([self.appkey, self.appsecret, self.account]):
                raise ValueError("Missing required configuration values")
            
            logger.info("Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _normalize_tr_id(self, tr_id: str) -> str:
        """TR ID를 환경에 맞게 정규화"""
        if self.env != "demo":
            return tr_id
        
        if tr_id and tr_id[0] in ("T", "J", "C"):
            return "V" + tr_id[1:]
        
        return tr_id
    
    def _authenticate(self) -> bool:
        """API 인증 수행"""
        try:
            url = f"{self.base_url}/oauth2/tokenP"
            
            headers = {
                "Content-Type": "application/json; charset=utf-8"
            }
            
            data = {
                "grant_type": "client_credentials",
                "appkey": self.appkey,
                "appsecret": self.appsecret
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            self.access_token = result.get("access_token")
            
            if not self.access_token:
                self.add_result("Authentication", False, "No access token received")
                return False
            
            self.add_result(
                "Authentication", 
                True, 
                "Successfully obtained access token",
                {"token_length": len(self.access_token)}
            )
            return True
            
        except Exception as e:
            self.add_result("Authentication", False, f"Authentication failed: {str(e)}")
            return False
    
    def _build_headers(self, tr_id: str) -> Dict[str, str]:
        """API 요청 헤더 생성"""
        if not self.access_token:
            raise ValueError("Not authenticated")
        
        tr_id = self._normalize_tr_id(tr_id)
        
        return {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self.access_token}",
            "appKey": self.appkey,
            "appSecret": self.appsecret,
            "tr_id": tr_id,
            "custtype": "P"
        }
    
    def _api_request(self, method: str, url: str, tr_id: str, params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Tuple[bool, Dict[str, Any], str]:
        """
        API 요청을 실행하고 결과를 반환
        Returns:
            (success, data, error_message)
        """
        try:
            headers = self._build_headers(tr_id)
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=15)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=json_data, timeout=15)
            else:
                return False, {}, f"Unsupported method: {method}"
            
            response.raise_for_status()
            data = response.json()
            
            # API 응답 검증
            rt_cd = data.get('rt_cd', '')
            if rt_cd != '0':
                error_msg = data.get('msg1', data.get('msg', 'Unknown error'))
                return False, data, f"API error: {error_msg} (rt_cd={rt_cd})"
            
            return True, data, ""
            
        except requests.exceptions.Timeout:
            return False, {}, "Request timeout"
        except requests.exceptions.HTTPError as e:
            return False, {}, f"HTTP error: {str(e)}"
        except requests.exceptions.RequestException as e:
            return False, {}, f"Request error: {str(e)}"
        except Exception as e:
            return False, {}, f"Unexpected error: {str(e)}"
    
    def add_result(self, test_name: str, success: bool, message: str, details: Optional[Dict] = None, error_details: Optional[str] = None):
        """테스트 결과 추가"""
        self.test_count += 1
        if success:
            self.success_count += 1
            
        result = {
            'test_name': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
            'error_details': error_details
        }
        self.results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} {test_name}: {message}")
    
    def test_account_balance_variations(self) -> int:
        """계좌 잔고 조회 다양한 방법으로 테스트"""
        success_count = 0
        
        # 방법 1: CTRP6504R (기본 계좌잔고 조회)
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            params = {
                "cano": self.account[:8],
                "acnt_prdt_cd": self.product,
                "afhr_flpr_yn": "N",
                "fank_sum_ord_tp_code": "00",
                "fun_dvsn": "00",
                "plov_dvsn": "00",
                "tr_crdt_type_cd": "00",
                "cdd_dvsn": "00"
            }
            
            success, data, error = self._api_request('GET', url, "CTRP6504R", params=params)
            
            if success:
                output1 = data.get('output1', [])
                output2 = data.get('output2', [])
                cash_amount = "0"
                if output2:
                    cash_amount = output2[0].get('dnca_tot_amt', '0')
                
                self.add_result(
                    "Account Balance (CTRP6504R)", 
                    True,
                    f"Success with cash: {cash_amount}",
                    {"cash": cash_amount, "holdings_count": len(output1)}
                )
                success_count += 1
            else:
                self.add_result(
                    "Account Balance (CTRP6504R)", 
                    False,
                    error,
                    error_details=str(data)
                )
        
        except Exception as e:
            self.add_result("Account Balance (CTRP6504R)", False, f"Exception: {str(e)}")
        
        # 방법 2: TTTC8434R (보유종목 조회로 계좌정보 획득)
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            params = {
                "cano": self.account[:8],
                "acnt_prdt_cd": self.product,
                "afhr_flpr_yn": "N",
                "unpr": "",
                "fund_sttl_icld_yn": "N",
                "fncg_ami_auto_rdpt_yn": "N",
                "prcs_dvsn": "01",
                "cost_icld_yn": "N",
                "ctx_area_fk100": "",
                "ctx_area_nk100": ""
            }
            
            success, data, error = self._api_request('GET', url, "TTTC8434R", params=params)
            
            if success:
                output1 = data.get('output1', [])
                output2 = data.get('output2', [])
                holdings = [item for item in output1 if float(item.get('hldg_qty', '0')) > 0]
                
                # output2에서 계좌 정보 추출
                account_info = output2[0] if output2 else {}
                total_assets = account_info.get('tot_evlu_amt', '0')
                cash_amount = account_info.get('dnca_tot_amt', '0')
                
                self.add_result(
                    "Account Info via Holdings (TTTC8434R)",
                    True,
                    f"Holdings: {len(holdings)}, Total: {total_assets}, Cash: {cash_amount}",
                    {
                        "holdings_count": len(holdings),
                        "total_assets": total_assets,
                        "cash": cash_amount,
                        "has_account_summary": bool(output2)
                    }
                )
                success_count += 1
            else:
                self.add_result(
                    "Account Info via Holdings (TTTC8434R)",
                    False,
                    error,
                    error_details=str(data)
                )
        
        except Exception as e:
            self.add_result("Account Info via Holdings (TTTC8434R)", False, f"Exception: {str(e)}")
        
        return success_count
    
    def test_stock_prices_multiple(self) -> int:
        """여러 종목의 가격 조회 테스트"""
        success_count = 0
        failed_tickers = []
        successful_tickers = []
        
        for ticker in self.test_tickers:
            try:
                url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
                params = {
                    "fid_cond_mrkt_div_code": "J",
                    "fid_input_iscd": ticker
                }
                
                success, data, error = self._api_request('GET', url, "FHKST01010100", params=params)
                
                if success:
                    output = data.get('output', {})
                    current_price = output.get('stck_prpr', '0')
                    company_name = output.get('prdy_nmix', 'N/A')
                    
                    successful_tickers.append({
                        'ticker': ticker,
                        'price': current_price,
                        'name': company_name
                    })
                    success_count += 1
                else:
                    failed_tickers.append({'ticker': ticker, 'error': error})
                
                # API 호출 간격 (Rate Limiting 방지)
                time.sleep(0.1)
                
            except Exception as e:
                failed_tickers.append({'ticker': ticker, 'error': str(e)})
            
        # 결과 정리
        self.add_result(
            "Multiple Stock Prices",
            success_count > 0,
            f"Success: {success_count}/{len(self.test_tickers)} tickers",
            {
                "successful_tickers": successful_tickers,
                "failed_tickers": failed_tickers,
                "success_rate": f"{success_count/len(self.test_tickers)*100:.1f}%"
            }
        )
        
        return success_count
    
    def test_order_validation(self) -> int:
        """주문 관련 API 테스트 (실제 주문 없이 validation만)"""
        success_count = 0
        
        # 1. 주문 조회 테스트
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-orders"
            today = datetime.now().strftime("%Y%m%d")
            
            params = {
                "cano": self.account[:8],
                "acnt_prdt_cd": self.product,
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
            
            success, data, error = self._api_request('GET', url, "TTTC8434R", params=params)
            
            if success:
                orders = data.get('output', [])
                self.add_result(
                    "Order Inquiry",
                    True,
                    f"Retrieved {len(orders)} orders for today",
                    {"order_count": len(orders)}
                )
                success_count += 1
            else:
                self.add_result("Order Inquiry", False, error)
        
        except Exception as e:
            self.add_result("Order Inquiry", False, f"Exception: {str(e)}")
        
        # 2. 주문 가능 수량 조회
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-psbl-order"
            
            params = {
                "cano": self.account[:8],
                "acnt_prdt_cd": self.product,
                "pdno": "005930",  # 삼성전자
                "ord_unpr": "160000",
                "ord_dvsn": "00",  # 지정가
                "cma_evlu_amt_icld_yn": "Y",
                "ovrs_icld_yn": "N"
            }
            
            success, data, error = self._api_request('GET', url, "TTTC8908R", params=params)
            
            if success:
                output = data.get('output', {})
                max_qty = output.get('ord_psbl_qty', '0')
                self.add_result(
                    "Order Quantity Check",
                    True,
                    f"Max orderable quantity for 005930: {max_qty}",
                    {"max_quantity": max_qty, "ticker": "005930"}
                )
                success_count += 1
            else:
                self.add_result("Order Quantity Check", False, error)
        
        except Exception as e:
            self.add_result("Order Quantity Check", False, f"Exception: {str(e)}")
        
        return success_count
    
    def test_market_data(self) -> int:
        """시장 데이터 관련 API 테스트"""
        success_count = 0
        
        # 1. 휴장일 조회
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/chk-holiday"
            today = datetime.now().strftime("%Y%m%d")
            
            params = {
                "base_dt": today,
                "ctx_area_nk": "",
                "ctx_area_fk": ""
            }
            
            success, data, error = self._api_request('GET', url, "CTCA0903R", params=params)
            
            if success:
                holidays = data.get('output', [])
                self.add_result(
                    "Holiday Check",
                    True,
                    f"Holiday data retrieved: {len(holidays)} entries",
                    {"holiday_count": len(holidays)}
                )
                success_count += 1
            else:
                self.add_result("Holiday Check", False, error)
        
        except Exception as e:
            self.add_result("Holiday Check", False, f"Exception: {str(e)}")
        
        # 2. 시장 운영 시간 조회
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"
            
            params = {
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": "005930",
                "fid_input_hour_1": "1",
                "fid_pw_data_incu_yn": "Y"
            }
            
            success, data, error = self._api_request('GET', url, "FHKST03010200", params=params)
            
            if success:
                output = data.get('output2', [])
                self.add_result(
                    "Market Time Data",
                    True,
                    f"Time data retrieved: {len(output)} entries",
                    {"time_data_count": len(output)}
                )
                success_count += 1
            else:
                self.add_result("Market Time Data", False, error)
        
        except Exception as e:
            self.add_result("Market Time Data", False, f"Exception: {str(e)}")
        
        return success_count
    
    def test_extended_apis(self) -> int:
        """확장된 API 테스트"""
        success_count = 0
        
        # 1. 종목 검색
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/search-stock-info"
            
            params = {
                "prdt_type_cd": "300",
                "micr_tp_cd": "E",
                "prdt_name": "삼성",
                "prdt_name_eng": "",
                "prdt_shrn_cd": "",
                "std_pdno": "",
                "schd_div_cd": ""
            }
            
            success, data, error = self._api_request('GET', url, "CTPF1604R", params=params)
            
            if success:
                output = data.get('output', [])
                self.add_result(
                    "Stock Search",
                    True,
                    f"Found {len(output)} stocks matching '삼성'",
                    {"search_results": len(output)}
                )
                success_count += 1
            else:
                self.add_result("Stock Search", False, error)
        
        except Exception as e:
            self.add_result("Stock Search", False, f"Exception: {str(e)}")
        
        return success_count
    
    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """포괄적 테스트 실행"""
        logger.info("🔍 Starting comprehensive KIS API tests...")
        
        # 인증 테스트
        if not self._authenticate():
            logger.error("❌ Authentication failed - stopping all tests")
            return self._generate_report()
        
        # 각 카테고리별 테스트
        test_categories = {
            "Account Balance Variations": self.test_account_balance_variations,
            "Multiple Stock Prices": self.test_stock_prices_multiple,
            "Order Validation": self.test_order_validation,
            "Market Data": self.test_market_data,
            "Extended APIs": self.test_extended_apis
        }
        
        category_results = {}
        for category, test_func in test_categories.items():
            logger.info(f"🧪 Testing {category}...")
            try:
                success_count = test_func()
                category_results[category] = success_count
                logger.info(f"✅ {category}: {success_count} successful tests")
            except Exception as e:
                logger.error(f"❌ {category} failed with error: {e}")
                category_results[category] = 0
            
            # 카테고리 간 대기 시간 (API Rate Limiting)
            time.sleep(1)
        
        logger.info(f"🏁 Comprehensive tests completed: {self.success_count}/{self.test_count} passed")
        
        return self._generate_report(category_results)
    
    def _generate_report(self, category_results: Optional[Dict] = None) -> Dict[str, Any]:
        """상세 보고서 생성"""
        total_tests = len(self.results)
        passed_tests = sum(1 for result in self.results if result['success'])
        failed_tests = total_tests - passed_tests
        
        # 실패한 테스트들 분류
        failed_by_error = {}
        for result in self.results:
            if not result['success']:
                error_key = result['message'].split(':')[0] if ':' in result['message'] else result['message']
                if error_key not in failed_by_error:
                    failed_by_error[error_key] = []
                failed_by_error[error_key].append(result['test_name'])
        
        return {
            "summary": {
                "environment": self.env,
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": passed_tests / total_tests if total_tests > 0 else 0,
                "category_results": category_results or {}
            },
            "failed_by_error_type": failed_by_error,
            "detailed_results": self.results
        }
    
    def print_detailed_summary(self, report: Dict[str, Any]):
        """상세 결과 출력"""
        summary = report["summary"]
        failed_by_error = report["failed_by_error_type"]
        
        print("\n" + "="*80)
        print(f"📊 COMPREHENSIVE KIS API TEST REPORT ({self.env.upper()} Environment)")
        print("="*80)
        
        print(f"🕒 Test Time: {summary['timestamp']}")
        print(f"📈 Total Tests: {summary['total_tests']}")
        print(f"✅ Passed: {summary['passed_tests']}")
        print(f"❌ Failed: {summary['failed_tests']}")
        print(f"📊 Success Rate: {summary['success_rate']*100:.1f}%")
        
        if summary.get('category_results'):
            print(f"\n📋 Category Results:")
            for category, success_count in summary['category_results'].items():
                print(f"  • {category}: {success_count} successes")
        
        if failed_by_error:
            print(f"\n❌ Failed Tests by Error Type:")
            for error_type, test_names in failed_by_error.items():
                print(f"  🚨 {error_type}:")
                for test_name in test_names:
                    print(f"    - {test_name}")
        
        print(f"\n📋 All Test Results:")
        for result in report["detailed_results"]:
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"  {status} {result['test_name']}: {result['message']}")
            
            if result['details']:
                for key, value in result['details'].items():
                    if isinstance(value, list) and len(value) > 3:
                        print(f"    - {key}: {len(value)} items")
                    else:
                        print(f"    - {key}: {value}")
        
        print("\n" + "="*80)
    
    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None):
        """보고서를 파일로 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_api_test_{self.env}_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"📄 Detailed report saved to: {filename}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")


def main():
    """메인 함수"""
    env = sys.argv[1] if len(sys.argv) > 1 else "demo"
    
    try:
        tester = ComprehensiveKISAPITester(env=env)
        report = tester.run_comprehensive_tests()
        
        tester.print_detailed_summary(report)
        tester.save_report(report)
        
        return 0 if report["summary"]["success_rate"] > 0.5 else 1
        
    except Exception as e:
        logger.error(f"Comprehensive test failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)