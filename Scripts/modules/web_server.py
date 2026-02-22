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
from flask import Flask, render_template, jsonify
import json
from pathlib import Path

from .config_loader import get_config
from .kis_auth import KISAuth
from .kis_portfolio_fetcher import KISPortfolioFetcher

logger = logging.getLogger(__name__)


class PortfolioWebServer:
    """포트폴리오 상태를 웹으로 표시하는 서버 클래스"""
    
    def __init__(self, port: int = 5000, host: str = "127.0.0.1", env: str = "demo"):
        """
        웹 서버 초기화
        
        Args:
            port (int): 서버 포트 번호
            host (str): 서버 호스트 주소
            env (str): 환경 설정 ('demo' 또는 'real')
        """
        self.port = port
        self.host = host
        self.env = env
        
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
                'api_status': 'connected' if self.kis_auth else 'disconnected'
            })
    
    def get_portfolio_data(self) -> Dict:
        """포트폴리오 데이터 조회 (캐시 적용)"""
        now = datetime.now()
        
        # 캐시된 데이터가 있고 유효한 경우 반환
        if (self._portfolio_cache and self._last_update and 
            (now - self._last_update).seconds < self._cache_duration):
            return self._portfolio_cache
        
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