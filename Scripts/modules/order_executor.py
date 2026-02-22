# -*- coding: utf-8 -*-
"""
Order Execution Module
실제 주문 실행: 리밸런싱 계획을 KIS API를 통해 주문으로 변환, 실행
Dry-run 모드도 지원
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .config_loader import PortfolioConfigLoader
from .kis_auth import KISAuth
from .portfolio_models import RebalancePlan, ExecutionResult, RebalanceOrder
from .kis_trading import KISTrading


logger = logging.getLogger(__name__)


class OrderExecutor:
    """주문 실행 엔진"""
    
    def __init__(
        self,
        config_loader: PortfolioConfigLoader,
        kis_auth: KISAuth
    ):
        """
        Args:
            config_loader (PortfolioConfigLoader): 설정 로더
            kis_auth (KISAuth): 인증 정보
        """
        self.config = config_loader
        self.kis_auth = kis_auth
        self.base_url = kis_auth.base_url
        
        # KISTrading 인스턴스 생성
        self.trading = KISTrading(kis_auth)
        
        # 설정 로드
        self.order_type = self.config.get_advanced("order_policy/order_type", "market")
        
        logger.info(f"OrderExecutor initialized: order_type={self.order_type}")
    
    
    def execute_plan(self, plan: RebalancePlan) -> ExecutionResult:
        """
        리밸런싱 계획을 실행합니다.
        매도 주문 먼저 실행 후 매수 주문 실행 (현금 확보).
        
        Args:
            plan (RebalancePlan): 리밸런싱 계획
            
        Returns:
            ExecutionResult: 실행 결과
        """
        result = ExecutionResult(
            portfolio_id=plan.portfolio_id,
            timestamp=datetime.now(),
            plan=plan
        )
        
        if not plan.should_rebalance:
            result.succeeded = True
            result.error_message = "No rebalancing needed"
            logger.info("Plan does not require rebalancing, skipping execution")
            return result
        
        logger.info(f"Executing rebalancing plan with {len(plan.orders)} orders")
        
        try:
            # 1. 매도 주문 먼저 실행 (현금 확보)
            sell_orders = [o for o in plan.orders if o.action == "sell"]
            for order in sell_orders:
                self._execute_order(order, result)
            
            # 2. 매수 주문 실행
            buy_orders = [o for o in plan.orders if o.action == "buy"]
            for order in buy_orders:
                self._execute_order(order, result)
            
            result.succeeded = True
            logger.info(f"Plan execution completed: {len(result.executed_orders)} orders executed")
            
        except Exception as e:
            result.succeeded = False
            result.error_message = str(e)
            logger.error(f"Error executing plan: {e}")
        
        return result
    
    def _execute_order(self, order: RebalanceOrder, result: ExecutionResult) -> None:
        """
        단일 주문을 실행합니다.
        
        Args:
            order (RebalanceOrder): 주문 정보
            result (ExecutionResult): 실행 결과 객체 (실행된 주문 추가)
        """
        if order.estimated_quantity <= 0:
            logger.warning(
                f"Skipping {order.action} order for {order.ticker}: "
                f"quantity={order.estimated_quantity}"
            )
            return

        logger.info(
            f"Executing {order.action} order for {order.ticker}: "
            f"qty={order.estimated_quantity}, "
            f"price={order.estimated_price:.2f}"
        )
        
        # 실전 모드: 실제 주문 실행
        self._execute_order_live(order, result)
    
    def _execute_order_live(self, order: RebalanceOrder, result: ExecutionResult) -> None:
        """
        실전 모드에서 실제 주문을 실행합니다.
        
        Args:
            order (RebalanceOrder): 주문 정보
            result (ExecutionResult): 실행 결과 객체
        """
        try:
            # KISTrading 모듈을 사용하여 주문 실행
            if self.order_type == "market":
                if order.action == "buy":
                    order_result = self.trading.buy_market_order(
                        stock_code=order.ticker,
                        quantity=order.estimated_quantity
                    )
                else:  # sell
                    order_result = self.trading.sell_market_order(
                        stock_code=order.ticker,
                        quantity=order.estimated_quantity
                    )
            else:  # limit order
                price = int(order.estimated_price)
                if order.action == "buy":
                    order_result = self.trading.buy_limit_order(
                        stock_code=order.ticker,
                        quantity=order.estimated_quantity,
                        price=price
                    )
                else:  # sell
                    order_result = self.trading.sell_limit_order(
                        stock_code=order.ticker,
                        quantity=order.estimated_quantity,
                        price=price
                    )
            
            # 주문 성공
            if order_result.get("success"):
                result.executed_orders.append(order_result)
                logger.info(f"Order placed successfully: {order_result}")
            else:
                # 상세한 에러 메시지 추출
                error_msg = order_result.get('message', 'Unknown error')
                logger.error(f"Order placement failed: {order_result}")
                raise RuntimeError(f"Order placement failed: {error_msg}")
        
        except Exception as e:
            # RuntimeError에서 KIS API 에러 메시지 추출
            error_msg = str(e)
            if isinstance(e, RuntimeError) and "Order placement failed:" in error_msg:
                # 이미 처리된 에러 메시지는 그대로 전달
                pass
            elif isinstance(e, RuntimeError) and "KIS API error" in error_msg:
                # KIS API 에러 메시지 추출
                if " - " in error_msg:
                    clean_msg = error_msg.split(" - ", 1)[1]
                    error_msg = f"Order placement failed: {clean_msg}"
                    
            logger.error(f"Error placing order for {order.ticker}: {error_msg}")
            raise RuntimeError(error_msg)
    
