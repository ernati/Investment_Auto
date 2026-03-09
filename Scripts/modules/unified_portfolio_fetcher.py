# -*- coding: utf-8 -*-
"""
Unified Portfolio Fetcher Module
KIS와 Upbit의 포트폴리오 데이터를 통합하여 조회하는 모듈

주요 기능:
- KIS 주식/채권 포트폴리오 조회
- Upbit 비트코인 포트폴리오 조회
- 통합 포트폴리오 스냅샷 생성
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .config_loader import PortfolioConfigLoader
from .kis_auth import KISAuth
from .kis_portfolio_fetcher import KISPortfolioFetcher
from .upbit_api_client import UpbitClient, UpbitAuth, get_upbit_client
from .portfolio_models import PortfolioSnapshot, PositionSnapshot


logger = logging.getLogger(__name__)


# 코인 티커 상수
BITCOIN_TICKER = "bitcoin"


class UnifiedPortfolioFetcher:
    """KIS와 Upbit의 포트폴리오를 통합 조회하는 클래스"""
    
    def __init__(
        self,
        kis_auth: KISAuth,
        upbit_client: Optional[UpbitClient] = None,
        env: str = "demo"
    ):
        """
        Args:
            kis_auth (KISAuth): KIS 인증 정보
            upbit_client (UpbitClient, optional): Upbit 클라이언트
            env (str): 환경 설정 ('real' 또는 'demo')
        """
        self.kis_fetcher = KISPortfolioFetcher(kis_auth)
        self.env = env
        
        # Upbit 클라이언트 설정
        if upbit_client:
            self.upbit_client = upbit_client
        else:
            self.upbit_client = get_upbit_client(env)
        
        logger.info(f"UnifiedPortfolioFetcher 초기화: env={env}")
    
    def fetch_unified_portfolio_snapshot(
        self,
        portfolio_id: str,
        price_source: str = "last",
        extra_tickers: Optional[List[str]] = None
    ) -> PortfolioSnapshot:
        """
        KIS와 Upbit의 통합 포트폴리오 스냅샷을 생성합니다.
        
        Args:
            portfolio_id (str): 포트폴리오 ID
            price_source (str): 가격 소스 ("last" 또는 "close")
            extra_tickers (List[str], optional): 추가로 조회할 티커 목록
            
        Returns:
            PortfolioSnapshot: 통합 포트폴리오 스냅샷
        """
        logger.info(f"통합 포트폴리오 스냅샷 조회 시작: {portfolio_id}")
        
        # 1. KIS 포트폴리오 스냅샷 조회
        # 코인 티커는 제외하고 주식/채권만 조회
        stock_bond_tickers = []
        if extra_tickers:
            stock_bond_tickers = [t for t in extra_tickers if t != BITCOIN_TICKER]
        
        kis_snapshot = self.kis_fetcher.fetch_portfolio_snapshot(
            portfolio_id=portfolio_id,
            price_source=price_source,
            extra_tickers=stock_bond_tickers
        )
        
        logger.info(
            f"KIS 스냅샷 조회 완료: "
            f"현금={kis_snapshot.cash:,.0f}원, "
            f"주식가치={kis_snapshot.stocks_value:,.0f}원"
        )
        
        # 2. Upbit 계좌 정보 조회
        upbit_info = self.upbit_client.get_btc_evaluation()
        
        upbit_krw = 0.0
        upbit_btc_value = 0.0
        btc_balance = 0.0
        btc_price = 0.0
        
        if upbit_info.get("success"):
            upbit_krw = upbit_info.get("krw_balance", 0)
            upbit_btc_value = upbit_info.get("btc_value", 0)
            btc_balance = upbit_info.get("btc_balance", 0)
            btc_price = upbit_info.get("current_price", 0)
            
            logger.info(
                f"Upbit 스냅샷 조회 완료: "
                f"KRW={upbit_krw:,.0f}원, "
                f"BTC={btc_balance:.8f} (평가={upbit_btc_value:,.0f}원)"
            )
        else:
            logger.warning(f"Upbit 정보 조회 실패: {upbit_info.get('error')}")
        
        # 3. 통합 스냅샷 생성
        # 총 현금 = KIS 현금 + Upbit KRW
        total_cash = kis_snapshot.cash + upbit_krw
        
        # 기존 positions 복사
        unified_snapshot = PortfolioSnapshot(
            portfolio_id=portfolio_id,
            timestamp=datetime.now(),
            cash=total_cash
        )
        
        # KIS positions 추가
        for ticker, position in kis_snapshot.positions.items():
            unified_snapshot.positions[ticker] = position
        
        # Bitcoin position 추가 (보유 중이거나 목표 비중이 있는 경우)
        if btc_balance > 0 or (extra_tickers and BITCOIN_TICKER in extra_tickers):
            # 가격이 0이면 다시 조회
            if btc_price <= 0:
                price_info = self.upbit_client.get_bitcoin_price()
                if price_info.get("success"):
                    btc_price = price_info.get("trade_price", 0)
            
            if btc_price > 0:
                # 비트코인은 소수점 보유가 가능하므로 quantity를 float로 처리
                # PositionSnapshot은 int를 기대하므로, 소수점 단위를 KRW로 환산
                # 평가액 = btc_balance * btc_price
                unified_snapshot.positions[BITCOIN_TICKER] = PositionSnapshot(
                    ticker=BITCOIN_TICKER,
                    quantity=1,  # 비트코인은 1단위로 표시 (실제 수량은 별도 추적)
                    price=btc_price
                )
                # evaluation을 실제 평가액으로 재설정
                unified_snapshot.positions[BITCOIN_TICKER].evaluation = upbit_btc_value
                
                # 비트코인 보유 수량 저장 (추후 주문 시 필요)
                unified_snapshot.positions[BITCOIN_TICKER]._btc_balance = btc_balance
        
        # total_value와 stocks_value 재계산
        unified_snapshot._recalculate()
        
        logger.info(
            f"통합 스냅샷 생성 완료: "
            f"총현금={total_cash:,.0f}원, "
            f"총자산={unified_snapshot.total_value:,.0f}원, "
            f"포지션수={len(unified_snapshot.positions)}"
        )
        
        return unified_snapshot
    
    def get_upbit_cash(self) -> float:
        """Upbit KRW 잔고를 반환합니다."""
        info = self.upbit_client.get_account_info()
        if info.get("success"):
            return info.get("krw", 0)
        return 0.0
    
    def get_bitcoin_info(self) -> Dict:
        """비트코인 정보를 반환합니다."""
        return self.upbit_client.get_btc_evaluation()
    
    def get_portfolio_snapshot(self) -> Dict:
        """
        웹 서버용 포트폴리오 스냅샷을 반환합니다.
        
        Returns:
            dict: 포트폴리오 스냅샷 딕셔너리
        """
        # KIS 잔고 및 보유 종목 조회
        kis_balance = self.kis_fetcher.fetch_account_balance()
        kis_holdings = self.kis_fetcher.fetch_holdings()
        
        kis_cash = kis_balance.get('cash', 0)
        
        # Upbit 정보 조회
        upbit_info = self.upbit_client.get_btc_evaluation()
        upbit_krw = upbit_info.get('krw_balance', 0) if upbit_info.get('success') else 0
        btc_balance = upbit_info.get('btc_balance', 0) if upbit_info.get('success') else 0
        btc_price = upbit_info.get('current_price', 0) if upbit_info.get('success') else 0
        btc_value = upbit_info.get('btc_value', 0) if upbit_info.get('success') else 0
        
        # 주식 정보 수집
        stocks = []
        total_stock_value = 0
        for ticker, quantity in kis_holdings.items():
            try:
                current_price = self.kis_fetcher.fetch_current_price(ticker)
                market_value = current_price * quantity
                total_stock_value += market_value
                stocks.append({
                    'ticker': ticker,
                    'name': ticker,  # TODO: 종목명 조회
                    'quantity': quantity,
                    'current_price': current_price,
                    'market_value': market_value
                })
            except Exception as e:
                logger.warning(f"Failed to fetch price for {ticker}: {e}")
        
        # 총 자산 계산
        total_cash = kis_cash + upbit_krw
        total_assets = total_cash + total_stock_value + btc_value
        
        return {
            'total_assets': total_assets,
            'cash': {
                'total': total_cash,
                'kis_krw': kis_cash,
                'upbit_krw': upbit_krw
            },
            'stocks': stocks,
            'bonds': [],  # TODO: 채권 지원
            'crypto': {
                'bitcoin': {
                    'quantity': btc_balance,
                    'current_price': btc_price,
                    'market_value': btc_value
                }
            }
        }


def create_unified_fetcher(
    kis_auth: KISAuth,
    env: str = "demo"
) -> UnifiedPortfolioFetcher:
    """
    통합 포트폴리오 페처를 생성합니다.
    
    Args:
        kis_auth (KISAuth): KIS 인증 정보
        env (str): 환경 설정 ('real' 또는 'demo')
        
    Returns:
        UnifiedPortfolioFetcher: 통합 페처 인스턴스
    """
    upbit_client = get_upbit_client(env)
    return UnifiedPortfolioFetcher(kis_auth, upbit_client, env)
