# -*- coding: utf-8 -*-
"""
Portfolio Rebalancing Application
포트폴리오 자동 리밸런싱 프로그램 메인 애플리케이션
KIS 주식/채권 + Upbit 비트코인 통합 리밸런싱 지원
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# 모듈 임포트 (Scripts/modules 경로)
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.config_loader import get_portfolio_config, get_config
from modules.config_validator import ConfigValidator
from modules.kis_auth import KISAuth
from modules.kis_portfolio_fetcher import KISPortfolioFetcher
from modules.unified_portfolio_fetcher import UnifiedPortfolioFetcher, create_unified_fetcher
from modules.upbit_api_client import get_upbit_client
from modules.scheduler import PortfolioScheduler
from modules.rebalancing_engine import RebalancingEngine
from modules.order_executor import OrderExecutor
from modules.market_hours import get_market_status, format_market_status
from modules.web_server import PortfolioWebServer

# DB 관련 모듈 (optional)
try:
    from modules.db_manager import DatabaseManager
    from modules.db_models import (
        TradingHistoryRecord, RebalancingLogRecord,
        PortfolioSnapshotRecord, SystemLogRecord
    )
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('portfolio_rebalancing.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class PortfolioRebalancingApp:
    """포트폴리오 자동 리밸런싱 애플리케이션"""
    
    def __init__(self, skip_schedule_check: bool = False, env: str = None, enable_web: bool = True, web_port: int = 5000, db_enabled: bool = False):
        """
        애플리케이션 초기화
        
        Args:
            skip_schedule_check (bool): 스케줄러 체크를 건너뛸지 여부 (기본값: False)
            env (str): 환경 설정 ('real' 또는 'demo'), None이면 설정 파일에서 읽음
            enable_web (bool): 웹 서버 활성화 여부 (기본값: True)
            web_port (int): 웹 서버 포트 (기본값: 5000)
            db_enabled (bool): 데이터베이스 저장 활성화 여부 (기본값: False)
        """
        self.skip_schedule_check = skip_schedule_check
        self.enable_web = enable_web
        self.web_port = web_port
        self.db_enabled = db_enabled
        logger.info(f"Starting Portfolio Rebalancing Application (DB: {'enabled' if db_enabled else 'disabled'})")
        
        # 1. 설정 로드
        self.config = get_portfolio_config()
        self.config.load()
        logger.info("Configuration loaded successfully")
        
        # 환경 설정 (명령줄 우선, 없으면 설정 파일에서)
        if env:
            kis_env = env
            logger.info(f"Using environment from command line: {kis_env}")
        else:
            kis_env = self.config.get_basic("kis/env", "demo")
            logger.info(f"Using environment from config file: {kis_env}")
        
        # 1-1. 로드된 설정값 출력
        print("\n🔧 프로그램 시작 - 로드된 설정 정보")
        print("=" * 80)
        self.config.print_loaded_config()
        
        # KIS 설정도 출력
        kis_config_loader = get_config()
        kis_config_loader.load()
        print(f"\n🔑 KIS API 설정 (환경: {kis_env.upper()} {'(모의투자)' if kis_env == 'demo' else '(실전투자)'})")
        print("=" * 80)
        kis_config_loader.print_loaded_config()
        
        print("✅ 모든 설정이 성공적으로 로드되었습니다. 프로그램을 시작합니다.\n")
        
        # 2. 설정 검증
        validator = ConfigValidator(self.config)
        success, errors, warnings = validator.validate()
        validator.print_report()
        
        if not success:
            logger.error("Configuration validation failed. Exiting.")
            raise RuntimeError("Configuration validation failed")
        
        # 3. 인증 설정
        # kis_env는 이미 위에서 설정됨
        kis_config = get_config().get_kis_config(kis_env)

        appkey = kis_config.get("appkey")
        appsecret = kis_config.get("appsecret")
        account = kis_config.get("account")
        product = kis_config.get("product", "01")
        htsid = kis_config.get("htsid", "")
        
        self.kis_auth = KISAuth(
            appkey=appkey,
            appsecret=appsecret,
            account=account,
            product=product,
            htsid=htsid,
            env=kis_env
        )
        logger.info("KIS Authentication initialized")
        
        # 4. 각 모듈 초기화
        # Upbit 클라이언트 초기화
        self.upbit_client = get_upbit_client(kis_env)
        logger.info("Upbit client initialized")
        
        # 해외주식 설정 가져오기
        target_weights = self.config.get("target_weights", {})
        overseas_stocks_config = target_weights.get("overseas_stocks", {})
        if overseas_stocks_config:
            logger.info(f"Overseas stocks config loaded: {list(overseas_stocks_config.keys())}")
        
        # 통합 포트폴리오 페처 초기화 (KIS + Upbit + 해외주식)
        self.portfolio_fetcher = create_unified_fetcher(
            self.kis_auth, 
            kis_env, 
            overseas_stocks_config=overseas_stocks_config
        )
        logger.info("Unified portfolio fetcher initialized (KIS + Upbit + Overseas)")
        
        self.scheduler = PortfolioScheduler(self.config)
        self.rebalancing_engine = RebalancingEngine(self.config)
        
        # 주문 실행기 초기화 (Upbit 클라이언트 포함)
        self.order_executor = OrderExecutor(
            self.config, 
            self.kis_auth, 
            upbit_client=self.upbit_client,
            env=kis_env
        )

        # 5. 웹 서버 초기화 (선택사항)
        self.web_server = None
        if self.enable_web:
            try:
                self.web_server = PortfolioWebServer(
                    port=self.web_port,
                    host="127.0.0.1",
                    env=kis_env,
                    unified_fetcher=self.portfolio_fetcher  # KIS + Upbit 통합 페처 전달
                )
                logger.info(f"Web server initialized on port {self.web_port}")
            except Exception as e:
                logger.warning(f"Web server initialization failed: {e}")
                self.web_server = None
        
        # 6. 데이터베이스 매니저 초기화 (선택사항)
        self.db_manager = None
        if self.db_enabled:
            if not DB_AVAILABLE:
                logger.error("Database modules not available. Install psycopg2-binary.")
                raise RuntimeError("Database modules not available")
            
            try:
                self.db_manager = DatabaseManager()
                if self.db_manager.test_connection():
                    self.db_manager.create_tables()
                    logger.info("Database manager initialized and tables created")
                else:
                    logger.error("Database connection test failed")
                    self.db_manager = None
            except Exception as e:
                logger.warning(f"Database initialization failed: {e}")
                self.db_manager = None

        # 장 시간 체크 설정 (기본: 활성화)
        self.market_hours_enabled = self.config.get_basic(
            "rebalance/schedule/market_hours/enabled",
            True
        )
        
        logger.info("All modules initialized successfully")
    
    def run_once(self) -> bool:
        """
        한 번의 리밸런싱 사이클을 실행합니다.
        
        Returns:
            bool: 성공 여부
        """
        try:
            logger.info("Running rebalancing cycle")
            
            # 1. 실행 시간 확인 (skip_schedule_check가 False인 경우만)
            if not self.skip_schedule_check and not self.scheduler.is_execution_time():
                logger.debug("Not an execution time, skipping")
                return False

            # 1-1. 장 시간 확인
            if self.market_hours_enabled:
                market_status = get_market_status(timezone=self.scheduler.timezone_str)
                if not market_status.is_open:
                    logger.info(
                        "Market is closed, skipping rebalancing cycle: "
                        f"{format_market_status(market_status)}"
                    )
                    return False
            
            # 2. 포트폴리오 스냅샷 생성 (KIS + Upbit 통합)
            portfolio_id = self.config.get_basic("portfolio_id")
            target_weights = self.config.get_basic("target_weights", {})
            
            # 중첩된 target_weights에서 모든 ticker 추출 (stocks, bonds, coin)
            all_tickers = []
            for category, assets in target_weights.items():
                if isinstance(assets, dict):
                    all_tickers.extend(assets.keys())
            
            # 통합 포트폴리오 스냅샷 조회 (KIS 주식/채권 + Upbit 비트코인)
            portfolio_snapshot = self.portfolio_fetcher.fetch_unified_portfolio_snapshot(
                portfolio_id,
                price_source=self.config.get_basic("rebalance/price_source", "last"),
                extra_tickers=all_tickers
            )
            
            # 3. 리밸런싱 계획 생성
            plan = self.rebalancing_engine.create_rebalance_plan(portfolio_snapshot)
            
            if not plan.should_rebalance:
                logger.info(f"Rebalancing not needed: {plan.rebalance_reason}")
                return False
            
            # 4. 가드레일 적용 (한도 초과 시 스킵 대신 점진적 조정)
            adjusted_plan, guardrail_message = self.rebalancing_engine.apply_guardrails(plan)
            logger.info(f"Guardrails result: {guardrail_message}")
            
            # 조정 후 주문이 없으면 스킵
            if adjusted_plan.total_orders == 0:
                logger.info("No orders to execute after guardrail adjustment")
                return False
            
            # 5. 조정된 계획으로 주문 실행
            result = self.order_executor.execute_plan(adjusted_plan)
            
            if result.succeeded:
                logger.info(f"Plan executed successfully: {len(result.executed_orders)} orders")
                self.scheduler.record_execution()
                
                # 6. DB 저장 (db_enabled인 경우)
                if self.db_manager:
                    self._save_to_database(portfolio_snapshot, adjusted_plan, result)
                
                return True
            else:
                logger.error(f"Plan execution failed: {result.error_message}")
                
                # 실패 시에도 리밸런싱 로그 저장
                if self.db_manager:
                    self._save_rebalancing_log(portfolio_snapshot.portfolio_id, adjusted_plan, result)
                
                return False
        
        except Exception as e:
            logger.error(f"Error in rebalancing cycle: {e}", exc_info=True)
            return False
    
    def run_scheduler(self, check_interval: int = 60) -> None:
        """
        스케줄러를 실행합니다 (무한 루프).
        
        Args:
            check_interval (int): 체크 간격 (초, 기본값: 60초)
        """
        import time
        
        logger.info(f"Starting scheduler with {check_interval}s check interval")
        
        # 웹 서버 시작
        if self.web_server:
            try:
                self.web_server.start()
                if self.web_server.is_running():
                    logger.info(f"📊 Portfolio dashboard: http://127.0.0.1:{self.web_port}")
                    logger.info("🔄 Web server started alongside rebalancing scheduler")
            except Exception as e:
                logger.error(f"Failed to start web server: {e}")
        
        try:
            while True:
                self.run_once()
                next_execution = self.scheduler.get_next_execution_time()
                if next_execution:
                    logger.info(f"Next execution scheduled: {next_execution}")
                
                time.sleep(check_interval)
        
        except KeyboardInterrupt:
            logger.info("Scheduler interrupted by user")
        except Exception as e:
            logger.error(f"Fatal error in scheduler: {e}", exc_info=True)
            raise
        finally:
            # 웹 서버 중지
            if self.web_server:
                try:
                    self.web_server.stop()
                    logger.info("Web server stopped")
                except Exception as e:
                    logger.error(f"Error stopping web server: {e}")
    
    def _save_to_database(self, portfolio_snapshot, plan, result):
        """데이터베이스에 거래 및 리밸런싱 정보 저장"""
        try:
            env = self.kis_auth.env
            
            # positions 데이터 안전하게 변환 (PositionSnapshot 객체들을 dict로 변환)
            positions_data = {}
            for ticker, position in portfolio_snapshot.positions.items():
                if hasattr(position, 'to_dict'):
                    positions_data[ticker] = position.to_dict()
                elif isinstance(position, dict):
                    positions_data[ticker] = position
                else:
                    # fallback: 기본 속성들 추출
                    positions_data[ticker] = {
                        "ticker": getattr(position, 'ticker', ticker),
                        "quantity": getattr(position, 'quantity', 0),
                        "price": getattr(position, 'price', 0),
                        "evaluation": getattr(position, 'evaluation', 0)
                    }
            
            # 포트폴리오 스냅샷 저장
            snapshot_record = PortfolioSnapshotRecord(
                portfolio_id=portfolio_snapshot.portfolio_id,
                total_value=float(portfolio_snapshot.total_value),
                positions=positions_data,
                environment=env
            )
            self.db_manager.save_portfolio_snapshot(snapshot_record)
            
            # 거래 기록 저장 (executed_orders는 List[Dict] 타입)
            for order in result.executed_orders:
                # dict 또는 객체 모두 지원
                symbol = order.get('symbol') if isinstance(order, dict) else getattr(order, 'symbol', '')
                side = order.get('side') if isinstance(order, dict) else getattr(order, 'side', 'buy')
                quantity = order.get('quantity', 0) if isinstance(order, dict) else getattr(order, 'quantity', 0)
                price = order.get('price', 0) if isinstance(order, dict) else getattr(order, 'price', 0)
                order_id = order.get('order_id', '') if isinstance(order, dict) else getattr(order, 'order_id', '')
                
                trading_record = TradingHistoryRecord(
                    portfolio_id=portfolio_snapshot.portfolio_id,
                    symbol=symbol,
                    order_type='buy' if side == 'buy' else 'sell',
                    quantity=float(quantity) if quantity else 0.0,
                    price=float(price) if price else 0.0,
                    total_amount=float(quantity * price) if quantity and price else 0.0,
                    commission=0.0,  # 수수료 정보가 있다면 추가
                    order_id=str(order_id) if order_id else '',
                    status='completed',
                    environment=env
                )
                self.db_manager.save_trading_history(trading_record)
            
            # 리밸런싱 로그 저장
            self._save_rebalancing_log(portfolio_snapshot.portfolio_id, plan, result)
            
            logger.info(f"Successfully saved {len(result.executed_orders)} trading records to database")
        
        except Exception as e:
            logger.error(f"Failed to save data to database: {e}")
    
    def _save_rebalancing_log(self, portfolio_id, plan, result):
        """리밸런싱 로그 저장"""
        try:
            # plan 객체에서 weights 데이터 안전하게 추출
            target_weights = getattr(plan, 'target_weights', None) or {}
            current_weights = getattr(plan, 'current_weights', None) or {}
            
            # dict가 아닌 경우 변환 시도
            if not isinstance(target_weights, dict):
                target_weights = target_weights.to_dict() if hasattr(target_weights, 'to_dict') else {}
            if not isinstance(current_weights, dict):
                current_weights = current_weights.to_dict() if hasattr(current_weights, 'to_dict') else {}
            
            # after_weights: 실행 후 포트폴리오 스냅샷에서 계산
            after_weights = {}
            if result.succeeded and result.post_portfolio_snapshot:
                after_weights = result.post_portfolio_snapshot.get_current_weights()
            elif result.succeeded:
                # 스냅샷이 없으면 current_weights 사용 (변화 없음 가정)
                after_weights = current_weights
            
            # 상세한 리밸런싱 사유 생성
            detailed_reason = self._create_detailed_reason(plan, current_weights, target_weights)
            
            rebalancing_record = RebalancingLogRecord(
                portfolio_id=portfolio_id,
                rebalance_reason=detailed_reason,
                target_weights=target_weights,
                before_weights=current_weights,
                after_weights=after_weights,
                orders_executed=len(result.executed_orders) if result.succeeded else 0,
                status='success' if result.succeeded else 'failed',
                error_message=result.error_message if not result.succeeded else None,
                environment=self.kis_auth.env
            )
            self.db_manager.save_rebalancing_log(rebalancing_record)
        
        except Exception as e:
            logger.error(f"Failed to save rebalancing log: {e}")
    
    def _create_detailed_reason(self, plan, current_weights, target_weights) -> str:
        """상세한 리밸런싱 사유 생성"""
        reason = plan.rebalance_reason or "Unknown"
        
        # Band breach인 경우 어떤 종목이 벗어났는지 상세 정보 추가
        if "Band breach" in reason or "BAND" in reason:
            deviations = []
            band_value = self.rebalancing_engine.band_value
            
            for ticker, target_weight in target_weights.items():
                current_weight = current_weights.get(ticker, 0)
                deviation = current_weight - target_weight
                
                # 밴드 초과 여부 확인
                if abs(deviation) > band_value:
                    direction = "초과" if deviation > 0 else "미달"
                    deviations.append(
                        f"{ticker}: {current_weight*100:.1f}% (목표 {target_weight*100:.1f}%, {direction} {abs(deviation)*100:.1f}%p)"
                    )
            
            if deviations:
                reason = f"Band breach - {', '.join(deviations)}"
        
        return reason


def main():
    """메인 엔트리 포인트"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Portfolio Rebalancing System"
    )
    parser.add_argument(
        '--mode',
        choices=['once', 'schedule'],
        default='once',
        help='Execution mode: once (single run) or schedule (continuous)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (for schedule mode)'
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate configuration and exit'
    )
    parser.add_argument(
        '--skip-schedule-check',
        action='store_true',
        help='Skip scheduler check when running in once mode'
    )
    parser.add_argument(
        '--demo',
        action='store_true',
        help='Use demo (paper trading) mode instead of real trading'
    )
    parser.add_argument(
        '--disable-web',
        action='store_true',
        help='Disable web server'  
    )
    parser.add_argument(
        '--web-port',
        type=int,
        default=5000,
        help='Web server port (default: 5000)'
    )
    parser.add_argument(
        '--db-mode',
        action='store_true',
        help='Enable database logging and storage'
    )
    
    args = parser.parse_args()
    
    # 환경 설정
    env = "demo" if args.demo else "real"
    
    try:
        # 애플리케이션 초기화
        skip_schedule_check = args.skip_schedule_check or (args.mode == 'once')
        enable_web = not args.disable_web
        db_enabled = args.db_mode
        
        # DB 모드 활성화 시 정보 출력
        if db_enabled:
            logger.info("🗄️  Database mode enabled - All trading data will be stored")
        
        app = PortfolioRebalancingApp(
            skip_schedule_check=skip_schedule_check, 
            env=env,
            enable_web=enable_web,
            web_port=args.web_port,
            db_enabled=db_enabled
        )
        
        if args.validate_only:
            logger.info("Configuration validation completed successfully")
            return 0
        
        # 실행 모드 선택
        if args.mode == 'once':
            logger.info("Running single rebalancing cycle")
            success = app.run_once()
            return 0 if success else 1
        else:
            logger.info("Starting scheduler mode")
            app.run_scheduler(check_interval=args.interval)
            return 0
    
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
