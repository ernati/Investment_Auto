# -*- coding: utf-8 -*-
"""
Web Server Module
포트폴리오 상태를 웹으로 표시하는 서버 모듈
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
from flask import Flask, render_template, jsonify, request
import json
from pathlib import Path

from .config_loader import get_config
from .kis_auth import KISAuth
from .kis_portfolio_fetcher import KISPortfolioFetcher
from .db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class PortfolioWebServer:
    """포트폴리오 상태를 웹으로 표시하는 서버 클래스"""
    
    def __init__(
        self, 
        port: int = 5000, 
        host: str = "127.0.0.1", 
        env: str = "demo",
        unified_fetcher=None
    ):
        """
        웹 서버 초기화
        
        Args:
            port (int): 서버 포트 번호
            host (str): 서버 호스트 주소
            env (str): 환경 설정 ('demo' 또는 'real')
            unified_fetcher: UnifiedPortfolioFetcher 인스턴스 (KIS + Upbit 통합)
        """
        self.port = port
        self.host = host
        self.env = env
        self.unified_fetcher = unified_fetcher  # Upbit 포함 통합 페처
        
        # Flask 앱 초기화 (템플릿 경로 설정)
        template_dir = Path(__file__).parent.parent / "templates"
        self.app = Flask(__name__, template_folder=str(template_dir))
        self.running = False
        self.server_thread = None
        
        # KIS API 클라이언트 초기화
        try:
            config = get_config()
            kis_config = config.get_kis_config(env)
            self.kis_auth = KISAuth(
                appkey=kis_config["appkey"],
                appsecret=kis_config["appsecret"],
                account=kis_config["account"],
                product=kis_config["product"],
                htsid=kis_config["htsid"],
                env=env
            )
            self.portfolio_fetcher = KISPortfolioFetcher(self.kis_auth)
            logger.info(f"Web server initialized for {env} environment")
        except Exception as e:
            logger.error(f"Failed to initialize KIS API: {e}")
            self.kis_auth = None
            self.portfolio_fetcher = None
        
        # DB 매니저 초기화
        try:
            self.db_manager = DatabaseManager()
            logger.info("Database manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            self.db_manager = None
        
        # 라우트 설정
        self._setup_routes()
        
        # 포트폴리오 데이터 캐시
        self._portfolio_cache = None
        self._last_update = None
        self._cache_duration = 30  # 30초 캐시
    
    def _setup_routes(self):
        """웹 라우트 설정"""
        
        @self.app.route('/')
        def index():
            """메인 페이지"""
            return render_template('portfolio.html', env=self.env)
        
        @self.app.route('/api/portfolio')
        def get_portfolio_api():
            """포트폴리오 데이터 API"""
            try:
                data = self.get_portfolio_data()
                return jsonify(data)
            except Exception as e:
                logger.error(f"Portfolio API error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/health')
        def health_check():
            """헬스 체크 API"""
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'environment': self.env,
                'api_status': 'connected' if self.kis_auth else 'disconnected',
                'db_status': 'connected' if self.db_manager else 'disconnected'
            })
        
        @self.app.route('/api/db/trading-history')
        def get_trading_history_api():
            """
            거래 기록 조회 API
            
            Query Parameters:
                portfolio_id: 포트폴리오 ID ('all'이면 전체 조회, 기본값: 'all')
                environment: 환경 ('all'이면 전체 조회, 기본값: 'all')
                limit: 최대 조회 개수 (기본값: 50)
                offset: 시작 위치 (기본값: 0)
            """
            try:
                portfolio_id = request.args.get('portfolio_id', 'all')
                environment = request.args.get('environment', 'all')
                limit = int(request.args.get('limit', 50))
                offset = int(request.args.get('offset', 0))
                
                if not self.db_manager:
                    return jsonify({'error': 'Database not available'}), 500
                
                data = self.db_manager.get_trading_history(
                    portfolio_id, environment, limit, offset
                )
                return jsonify({
                    'data': data,
                    'total': len(data),
                    'limit': limit,
                    'offset': offset
                })
            except Exception as e:
                logger.error(f"Trading history API error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/db/rebalancing-logs')
        def get_rebalancing_logs_api():
            """
            리밸런싱 로그 조회 API
            
            Query Parameters:
                portfolio_id: 포트폴리오 ID ('all'이면 전체 조회, 기본값: 'all')
                environment: 환경 ('all'이면 전체 조회, 기본값: 'all')
                limit: 최대 조회 개수 (기본값: 30)
                offset: 시작 위치 (기본값: 0)
            """
            try:
                portfolio_id = request.args.get('portfolio_id', 'all')
                environment = request.args.get('environment', 'all')
                limit = int(request.args.get('limit', 30))
                offset = int(request.args.get('offset', 0))
                
                if not self.db_manager:
                    return jsonify({'error': 'Database not available'}), 500
                
                data = self.db_manager.get_rebalancing_logs(
                    portfolio_id, environment, limit, offset
                )
                return jsonify({
                    'data': data,
                    'total': len(data),
                    'limit': limit,
                    'offset': offset
                })
            except Exception as e:
                logger.error(f"Rebalancing logs API error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/db/portfolio-snapshots')
        def get_portfolio_snapshots_api():
            """
            포트폴리오 스냅샷 조회 API
            
            Query Parameters:
                portfolio_id: 포트폴리오 ID ('all'이면 전체 조회, 기본값: 'all')
                environment: 환경 ('all'이면 전체 조회, 기본값: 'all')
                limit: 최대 조회 개수 (기본값: 30)
                offset: 시작 위치 (기본값: 0)
            """
            try:
                portfolio_id = request.args.get('portfolio_id', 'all')
                environment = request.args.get('environment', 'all')
                limit = int(request.args.get('limit', 30))
                offset = int(request.args.get('offset', 0))
                
                if not self.db_manager:
                    return jsonify({'error': 'Database not available'}), 500
                
                data = self.db_manager.get_portfolio_snapshots(
                    portfolio_id, environment, limit, offset
                )
                return jsonify({
                    'data': data,
                    'total': len(data),
                    'limit': limit,
                    'offset': offset
                })
            except Exception as e:
                logger.error(f"Portfolio snapshots API error: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/db/system-logs')
        def get_system_logs_api():
            """시스템 로그 조회 API"""
            try:
                level = request.args.get('level', '')
                module = request.args.get('module', '')
                environment = request.args.get('environment', self.env)
                limit = int(request.args.get('limit', 50))
                offset = int(request.args.get('offset', 0))
                
                if not self.db_manager:
                    return jsonify({'error': 'Database not available'}), 500
                
                data = self.get_system_logs(level, module, environment, limit, offset)
                return jsonify({
                    'data': data,
                    'total': len(data),
                    'limit': limit,
                    'offset': offset
                })
            except Exception as e:
                logger.error(f"System logs API error: {e}")
                return jsonify({'error': str(e)}), 500
    
    def get_portfolio_data(self) -> Dict:
        """포트폴리오 데이터 조회 (캐시 적용)"""
        now = datetime.now()
        
        # 캐시된 데이터가 있고 유효한 경우 반환
        if (self._portfolio_cache and self._last_update and 
            (now - self._last_update).seconds < self._cache_duration):
            return self._portfolio_cache
        
        # UnifiedPortfolioFetcher가 있으면 통합 데이터 사용
        if self.unified_fetcher:
            return self._get_unified_portfolio_data(now)
        
        if not self.portfolio_fetcher:
            return {'error': 'KIS API not available'}
        
        try:
            # 계좌 잔고 조회
            balance_data = self.portfolio_fetcher.fetch_account_balance()
            
            # 보유 종목 조회
            holdings_data = self.portfolio_fetcher.fetch_holdings()
            
            # 종목별 현재가 조회 및 평가금액 계산
            positions = []
            total_stock_value = 0
            
            for ticker, quantity in holdings_data.items():
                try:
                    current_price = self.portfolio_fetcher.fetch_current_price(ticker)
                    market_value = current_price * quantity
                    total_stock_value += market_value
                    
                    positions.append({
                        'ticker': ticker,
                        'quantity': quantity,
                        'current_price': current_price,
                        'market_value': market_value
                    })
                except Exception as e:
                    logger.warning(f"Failed to fetch price for {ticker}: {e}")
                    positions.append({
                        'ticker': ticker,
                        'quantity': quantity,
                        'current_price': 0,
                        'market_value': 0
                    })
            
            # 총 자산 계산
            cash = balance_data.get('cash', 0)
            total_assets = cash + total_stock_value
            
            # 자산별 비율 계산
            if total_assets > 0:
                cash_ratio = (cash / total_assets) * 100
                for position in positions:
                    position['ratio'] = (position['market_value'] / total_assets) * 100
            else:
                cash_ratio = 0
                for position in positions:
                    position['ratio'] = 0
            
            # 결과 데이터 구성
            portfolio_data = {
                'timestamp': now.isoformat(),
                'environment': self.env,
                'account': self.kis_auth.account if self.kis_auth else 'N/A',
                'summary': {
                    'total_assets': total_assets,
                    'cash': cash,
                    'cash_ratio': cash_ratio,
                    'total_stock_value': total_stock_value,
                    'stock_ratio': ((total_stock_value / total_assets) * 100) if total_assets > 0 else 0
                },
                'positions': sorted(positions, key=lambda x: x['market_value'], reverse=True),
                'balance': balance_data
            }
            
            # 캐시 업데이트
            self._portfolio_cache = portfolio_data
            self._last_update = now
            
            logger.info(f"Portfolio data updated: {len(positions)} positions, total assets: {total_assets:,.0f}")
            return portfolio_data
            
        except Exception as e:
            logger.error(f"Failed to fetch portfolio data: {e}")
            return {
                'error': str(e),
                'timestamp': now.isoformat(),
                'environment': self.env
            }
    
    def _get_unified_portfolio_data(self, now: datetime) -> Dict:
        """
        통합 포트폴리오 데이터 조회 (KIS + Upbit)
        
        Args:
            now: 현재 시간
            
        Returns:
            dict: 통합 포트폴리오 데이터
        """
        try:
            # UnifiedPortfolioFetcher에서 스냅샷 가져오기
            snapshot = self.unified_fetcher.get_portfolio_snapshot()
            
            # 포지션 데이터 구성
            positions = []
            
            # 주식 포지션
            for stock in snapshot.get('stocks', []):
                positions.append({
                    'ticker': stock['ticker'],
                    'name': stock.get('name', stock['ticker']),
                    'category': 'stocks',
                    'quantity': stock['quantity'],
                    'current_price': stock['current_price'],
                    'market_value': stock['market_value'],
                    'ratio': 0  # 나중에 계산
                })
            
            # 채권 포지션
            for bond in snapshot.get('bonds', []):
                positions.append({
                    'ticker': bond['ticker'],
                    'name': bond.get('name', bond['ticker']),
                    'category': 'bonds',
                    'quantity': bond['quantity'],
                    'current_price': bond['current_price'],
                    'market_value': bond['market_value'],
                    'ratio': 0
                })
            
            # 비트코인 포지션
            bitcoin = snapshot.get('crypto', {}).get('bitcoin', {})
            if bitcoin.get('quantity', 0) > 0:
                positions.append({
                    'ticker': 'BTC',
                    'name': 'Bitcoin',
                    'category': 'crypto',
                    'quantity': bitcoin['quantity'],
                    'current_price': bitcoin['current_price'],
                    'market_value': bitcoin['market_value'],
                    'ratio': 0
                })
            
            # 현금 정보
            cash_info = snapshot.get('cash', {})
            kis_cash = cash_info.get('kis_krw', 0)
            upbit_krw = cash_info.get('upbit_krw', 0)
            total_cash = cash_info.get('total', kis_cash + upbit_krw)
            
            # 자산 합계
            total_stock_value = sum(p['market_value'] for p in positions if p['category'] == 'stocks')
            total_bond_value = sum(p['market_value'] for p in positions if p['category'] == 'bonds')
            total_crypto_value = sum(p['market_value'] for p in positions if p['category'] == 'crypto')
            total_assets = snapshot.get('total_assets', total_cash + total_stock_value + total_bond_value + total_crypto_value)
            
            # 비율 계산
            if total_assets > 0:
                cash_ratio = (total_cash / total_assets) * 100
                for position in positions:
                    position['ratio'] = (position['market_value'] / total_assets) * 100
            else:
                cash_ratio = 0
            
            # 결과 데이터 구성
            portfolio_data = {
                'timestamp': now.isoformat(),
                'environment': self.env,
                'account': self.kis_auth.account if self.kis_auth else 'N/A',
                'summary': {
                    'total_assets': total_assets,
                    'cash': total_cash,
                    'kis_cash': kis_cash,
                    'upbit_krw': upbit_krw,
                    'cash_ratio': cash_ratio,
                    'total_stock_value': total_stock_value,
                    'stock_ratio': ((total_stock_value / total_assets) * 100) if total_assets > 0 else 0,
                    'total_bond_value': total_bond_value,
                    'bond_ratio': ((total_bond_value / total_assets) * 100) if total_assets > 0 else 0,
                    'total_crypto_value': total_crypto_value,
                    'crypto_ratio': ((total_crypto_value / total_assets) * 100) if total_assets > 0 else 0,
                },
                'positions': sorted(positions, key=lambda x: x['market_value'], reverse=True),
                'balance': {
                    'total_cash': total_cash,
                    'kis_cash': kis_cash,
                    'upbit_krw': upbit_krw
                }
            }
            
            # 캐시 업데이트
            self._portfolio_cache = portfolio_data
            self._last_update = now
            
            logger.info(
                f"Unified portfolio data updated: {len(positions)} positions, "
                f"total assets: {total_assets:,.0f}, "
                f"KIS cash: {kis_cash:,.0f}, Upbit KRW: {upbit_krw:,.0f}"
            )
            return portfolio_data
            
        except Exception as e:
            logger.error(f"Failed to fetch unified portfolio data: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'timestamp': now.isoformat(),
                'environment': self.env
            }
    
    def start(self):
        """웹 서버 시작 (백그라운드 스레드)"""
        if self.running:
            logger.warning("Web server is already running")
            return
        
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        logger.info(f"Web server starting on http://{self.host}:{self.port}")
        
        # 서버가 시작될 때까지 잠시 대기
        time.sleep(2)
    
    def _run_server(self):
        """서버 실행 (내부 메서드)"""
        try:
            self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
        except Exception as e:
            logger.error(f"Web server error: {e}")
        finally:
            self.running = False
    
    def stop(self):
        """웹 서버 중지"""
        if self.running:
            self.running = False
            logger.info("Web server stopped")
    
    def is_running(self) -> bool:
        """서버 실행 상태 확인"""
        return self.running and self.server_thread and self.server_thread.is_alive()
    
    def get_system_logs(self, level: str = '', module: str = '', environment: str = '', 
                       limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        시스템 로그 조회 (필터링 지원)
        
        Args:
            level: 로그 레벨 필터
            module: 모듈 필터  
            environment: 환경 필터
            limit: 조회 제한 수
            offset: 오프셋
            
        Returns:
            시스템 로그 리스트
        """
        if not self.db_manager:
            return []
        
        try:
            with self.db_manager.get_connection() as conn:
                from psycopg2.extras import RealDictCursor
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    where_clauses = []
                    params = []
                    
                    if environment:
                        where_clauses.append("environment = %s")
                        params.append(environment)
                    
                    if level:
                        where_clauses.append("level = %s")
                        params.append(level)
                    
                    if module:
                        where_clauses.append("module ILIKE %s")
                        params.append(f"%{module}%")
                    
                    where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                    
                    query = f"""
                        SELECT * FROM system_logs
                        {where_sql}
                        ORDER BY timestamp DESC
                        LIMIT %s OFFSET %s
                    """
                    
                    params.extend([limit, offset])
                    cur.execute(query, params)
                    
                    return [dict(record) for record in cur.fetchall()]
                    
        except Exception as e:
            logger.error(f"Failed to get system logs: {e}")
            return []