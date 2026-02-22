# -*- coding: utf-8 -*-
"""
Portfolio Web Application
포트폴리오 상태를 웹으로 표시하는 애플리케이션
"""

import logging
import sys
import signal
import time
from pathlib import Path

# 모듈 임포트 (Scripts/modules 경로)
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.web_server import PortfolioWebServer

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('portfolio_web.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class PortfolioWebApp:
    """포트폴리오 웹 애플리케이션"""
    
    def __init__(self, port: int = 5000, host: str = "127.0.0.1", env: str = "demo"):
        """
        애플리케이션 초기화
        
        Args:
            port (int): 서버 포트 번호 (기본값: 5000)
            host (str): 서버 호스트 주소 (기본값: 127.0.0.1)
            env (str): 환경 설정 ('demo' 또는 'real', 기본값: demo)
        """
        self.port = port
        self.host = host
        self.env = env
        self.web_server = None
        
        # 시그널 핸들러 설정
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Portfolio Web App initialized for {env} environment on {host}:{port}")
    
    def _signal_handler(self, signum, frame):
        """시그널 핸들러 (Ctrl+C 등)"""
        logger.info("Shutdown signal received")
        self.stop()
        sys.exit(0)
    
    def start(self):
        """웹 애플리케이션 시작"""
        try:
            logger.info("Starting Portfolio Web Application...")
            
            # 웹 서버 초기화 및 시작
            self.web_server = PortfolioWebServer(
                port=self.port, 
                host=self.host, 
                env=self.env
            )
            
            self.web_server.start()
            
            if self.web_server.is_running():
                logger.info(f"✅ Web server started successfully!")
                logger.info(f"📊 Portfolio dashboard: http://{self.host}:{self.port}")
                logger.info(f"💻 Environment: {self.env.upper()}")
                logger.info(f"🔄 Press Ctrl+C to stop")
                
                # 서버가 실행되는 동안 대기
                try:
                    while self.web_server.is_running():
                        time.sleep(1)
                except KeyboardInterrupt:
                    logger.info("KeyboardInterrupt received")
            else:
                logger.error("Failed to start web server")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start application: {e}")
            return False
        
        return True
    
    def stop(self):
        """웹 애플리케이션 중지"""
        logger.info("Stopping Portfolio Web Application...")
        
        if self.web_server:
            self.web_server.stop()
            self.web_server = None
        
        logger.info("Portfolio Web Application stopped")
    
    def is_running(self) -> bool:
        """애플리케이션 실행 상태 확인"""
        return self.web_server and self.web_server.is_running()


def main():
    """메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Portfolio Web Application')
    parser.add_argument('--port', type=int, default=5000, help='서버 포트 번호 (기본값: 5000)')
    parser.add_argument('--host', type=str, default='127.0.0.1', help='서버 호스트 (기본값: 127.0.0.1)')
    parser.add_argument('--env', type=str, choices=['demo', 'real'], default='demo', 
                       help='환경 설정 (demo=모의, real=실제, 기본값: demo)')
    
    args = parser.parse_args()
    
    # 애플리케이션 시작
    app = PortfolioWebApp(port=args.port, host=args.host, env=args.env)
    app.start()


if __name__ == "__main__":
    main()