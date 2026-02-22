# -*- coding: utf-8 -*-
"""
Portfolio Data Models
포트폴리오 리밸런싱에 필요한 데이터 모델들
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class PriceSnapshot:
    """가격 스냅샷"""
    ticker: str          # 종목코드
    price: float         # 종목가격
    source: str = "last" # 가격 출처 ("close" 또는 "last")
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PositionSnapshot:
    """보유 포지션 스냅샷"""
    ticker: str          # 종목코드
    quantity: int        # 보유수량
    price: float         # 현재가
    evaluation: float = field(init=False)  # 평가금액 = 수량 * 가격
    
    def __post_init__(self):
        self.evaluation = self.quantity * self.price


@dataclass
class PortfolioSnapshot:
    """포트폴리오 전체 스냅샷"""
    portfolio_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 현금 정보
    cash: float = 0.0
    
    # 포지션 정보 (ticker -> PositionSnapshot)
    positions: Dict[str, PositionSnapshot] = field(default_factory=dict)
    
    # 계산된 값들
    total_value: float = field(init=False)
    stocks_value: float = field(init=False)
    
    def __post_init__(self):
        self._recalculate()
    
    def _recalculate(self):
        """포트폴리오 값을 재계산합니다."""
        self.stocks_value = sum(pos.evaluation for pos in self.positions.values())
        self.total_value = self.cash + self.stocks_value
    
    def add_position(self, ticker: str, quantity: int, price: float):
        """포지션을 추가합니다."""
        self.positions[ticker] = PositionSnapshot(ticker, quantity, price)
        self._recalculate()
    
    def update_position(self, ticker: str, quantity: int, price: float):
        """포지션을 업데이트합니다."""
        self.add_position(ticker, quantity, price)
    
    def update_cash(self, amount: float):
        """현금을 업데이트합니다."""
        self.cash = amount
        self._recalculate()
    
    def get_current_weight(self, ticker: str) -> float:
        """종목의 현재 비중을 반환합니다."""
        if self.total_value == 0:
            return 0.0
        if ticker not in self.positions:
            return 0.0
        return self.positions[ticker].evaluation / self.total_value
    
    def get_current_weights(self) -> Dict[str, float]:
        """모든 종목의 현재 비중을 반환합니다."""
        return {ticker: self.get_current_weight(ticker) for ticker in self.positions}


@dataclass
class RebalanceOrder:
    """리밸런싱 주문"""
    ticker: str          # 종목코드
    action: str          # 주문 방향 ("buy" 또는 "sell")
    target_value: float  # 목표 금액
    current_value: float # 현재 금액
    delta_value: float   # 필요한 변화량 (target - current)
    delta_weight: float  # 필요한 비중 변화
    
    # 주문 실행 관련
    estimated_quantity: int = 0   # 예상 수량
    estimated_price: float = 0.0  # 예상 가격


@dataclass
class RebalancePlan:
    """리밸런싱 계획"""
    portfolio_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 포트폴리오 스냅샷
    portfolio_snapshot: PortfolioSnapshot = None
    
    # 리밸런싱 판단
    should_rebalance: bool = False
    rebalance_reason: str = ""  # 리밸런싱 이유 (BAND, CALENDAR, HYBRID 등)
    
    # 주문 계획
    orders: List[RebalanceOrder] = field(default_factory=list)
    
    # 통계
    total_delta_value: float = 0.0  # 총 변화 금액
    total_orders: int = 0           # 총 주문 수


@dataclass
class ExecutionResult:
    """리밸런싱 실행 결과"""
    portfolio_id: str
    timestamp: datetime = field(default_factory=datetime.now)
    plan: RebalancePlan = None
    
    # 실행 상태
    succeeded: bool = False
    error_message: str = ""
    
    # 실행 주문들
    executed_orders: List[Dict] = field(default_factory=list)
    
    # 실행 후 포트폴리오 상태
    post_portfolio_snapshot: PortfolioSnapshot = None
