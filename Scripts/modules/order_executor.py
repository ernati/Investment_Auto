# -*- coding: utf-8 -*-
"""
Order Execution Module
실제 주문 실행: 리밸런싱 계획을 KIS API를 통해 주문으로 변환, 실행
Upbit를 통한 비트코인 주문도 지원
해외주식 주문도 지원 (KISOverseasTrading 사용)
Dry-run 모드도 지원
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .config_loader import PortfolioConfigLoader
from .kis_auth import KISAuth
from .portfolio_models import RebalancePlan, ExecutionResult, RebalanceOrder
from .kis_trading import KISTrading
from .kis_overseas_trading import KISOverseasTrading
from .upbit_api_client import UpbitClient, get_upbit_client
from .market_hours import is_overseas_market_open, get_overseas_market_status, format_market_status


logger = logging.getLogger(__name__)


# 코인 티커 상수
BITCOIN_TICKER = "bitcoin"


class OrderExecutor:
    """주문 실행 엔진 (KIS 국내주식/해외주식 + Upbit 비트코인)"""
    
    def __init__(
        self,
        config_loader: PortfolioConfigLoader,
        kis_auth: KISAuth,
        upbit_client: Optional[UpbitClient] = None,
        env: str = "demo"
    ):
        """
        Args:
            config_loader (PortfolioConfigLoader): 설정 로더
            kis_auth (KISAuth): KIS 인증 정보
            upbit_client (UpbitClient, optional): Upbit 클라이언트
            env (str): 환경 설정 ('real' 또는 'demo')
        """
        self.config = config_loader
        self.kis_auth = kis_auth
        self.base_url = kis_auth.base_url
        self.env = env
        
        # KISTrading 인스턴스 생성 (국내주식)
        self.trading = KISTrading(kis_auth)
        
        # KISOverseasTrading 인스턴스 생성 (해외주식)
        self.overseas_trading = KISOverseasTrading(kis_auth)
        
        # Upbit 클라이언트 설정
        if upbit_client:
            self.upbit_client = upbit_client
        else:
            self.upbit_client = get_upbit_client(env)
        
        # 설정 로드
        self.order_type = self.config.get_advanced("order_policy/order_type", "market")
        
        logger.info(f"OrderExecutor initialized: order_type={self.order_type}, env={env}")
    
    
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
        비트코인과 주식/채권을 구분하여 처리합니다.
        
        Args:
            order (RebalanceOrder): 주문 정보
            result (ExecutionResult): 실행 결과 객체 (실행된 주문 추가)
        """
        # 비트코인 주문인지 확인
        if order.ticker == BITCOIN_TICKER:
            self._execute_bitcoin_order(order, result)
            return
        
        # 주식/채권 주문
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
    
    def _execute_bitcoin_order(self, order: RebalanceOrder, result: ExecutionResult) -> None:
        """
        비트코인 주문을 실행합니다.
        
        Args:
            order (RebalanceOrder): 주문 정보
            result (ExecutionResult): 실행 결과 객체
        """
        try:
            if order.action == "buy":
                krw_amount = abs(order.delta_value)
                logger.info(f"Executing BTC BUY: {krw_amount:,.0f} KRW")
                
                order_result = self.upbit_client.buy_bitcoin(krw_amount)
                
                if order_result.get("success"):
                    result.executed_orders.append({
                        "symbol": BITCOIN_TICKER,
                        "side": "buy",
                        "quantity": order_result.get("btc_quantity", 0),
                        "price": order_result.get("current_price", 0),
                        "krw_amount": krw_amount,
                        "order_id": order_result.get("order_id", "demo"),
                        "is_demo": self.env == "demo"
                    })
                    logger.info(f"BTC buy order completed: {order_result}")
                else:
                    raise RuntimeError(f"BTC buy failed: {order_result.get('error')}")
                    
            else:  # sell
                # 매도할 BTC 수량 계산 (delta_value / current_price)
                btc_price = order.estimated_price
                btc_quantity = abs(order.delta_value) / btc_price if btc_price > 0 else 0
                
                logger.info(f"Executing BTC SELL: {btc_quantity:.8f} BTC")
                
                order_result = self.upbit_client.sell_bitcoin(btc_quantity)
                
                if order_result.get("success"):
                    result.executed_orders.append({
                        "symbol": BITCOIN_TICKER,
                        "side": "sell",
                        "quantity": order_result.get("btc_quantity", 0),
                        "price": order_result.get("current_price", 0),
                        "krw_received": order_result.get("krw_received", 0),
                        "pnl": order_result.get("pnl", 0),
                        "order_id": order_result.get("order_id", "demo"),
                        "is_demo": self.env == "demo"
                    })
                    logger.info(f"BTC sell order completed: {order_result}")
                else:
                    raise RuntimeError(f"BTC sell failed: {order_result.get('error')}")
                    
        except Exception as e:
            logger.error(f"Error executing BTC order: {e}")
            raise
    
    def _execute_order_live(self, order: RebalanceOrder, result: ExecutionResult) -> None:
        """
        실전 모드에서 실제 주문을 실행합니다.
        해외주식(exchange 필드가 있는 경우)과 국내주식을 구분하여 처리합니다.
        
        Args:
            order (RebalanceOrder): 주문 정보
            result (ExecutionResult): 실행 결과 객체
        """
        try:
            # 해외주식 여부 확인
            if order.exchange:
                order_result = self._execute_overseas_order(order)
            else:
                order_result = self._execute_domestic_order(order)
            
            # 해외 시장 휴장으로 스킵된 경우
            if order_result.get("skipped") and order_result.get("market_closed"):
                logger.info(
                    f"Skipped overseas order for {order.ticker}: market closed "
                    f"(exchange={order.exchange})"
                )
                # 스킵된 주문도 기록에 추가 (통계 목적)
                result.executed_orders.append({
                    **order_result,
                    "symbol": order.ticker,
                    "side": order.action,
                    "quantity": order.estimated_quantity
                })
                return  # 에러 없이 다음 주문으로 진행
            
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
    
    def _execute_domestic_order(self, order: RebalanceOrder) -> Dict:
        """
        국내주식 주문을 실행합니다.
        
        Args:
            order (RebalanceOrder): 주문 정보
            
        Returns:
            Dict: 주문 결과
        """
        if self.order_type == "market":
            if order.action == "buy":
                return self.trading.buy_market_order(
                    stock_code=order.ticker,
                    quantity=order.estimated_quantity
                )
            else:  # sell
                return self.trading.sell_market_order(
                    stock_code=order.ticker,
                    quantity=order.estimated_quantity
                )
        else:  # limit order
            price = int(order.estimated_price)
            if order.action == "buy":
                return self.trading.buy_limit_order(
                    stock_code=order.ticker,
                    quantity=order.estimated_quantity,
                    price=price
                )
            else:  # sell
                return self.trading.sell_limit_order(
                    stock_code=order.ticker,
                    quantity=order.estimated_quantity,
                    price=price
                )
    
    def _execute_overseas_order(self, order: RebalanceOrder) -> Dict:
        """
        해외주식 주문을 실행합니다.
        
        Note:
            해외주식 모의투자는 지정가 주문만 지원합니다.
            해당 거래소 시장이 열려있지 않으면 주문을 스킵합니다.
        
        Args:
            order (RebalanceOrder): 주문 정보
            
        Returns:
            Dict: 주문 결과
        """
        # 해외 거래소 시장 시간 체크
        if order.exchange:
            market_status = get_overseas_market_status(order.exchange)
            if not market_status.is_open:
                logger.warning(
                    f"Overseas market closed, skipping order for {order.ticker}: "
                    f"exchange={order.exchange}, {format_market_status(market_status)}"
                )
                return {
                    "success": False,
                    "order_no": "",
                    "message": f"해외 시장 휴장: {order.exchange} ({market_status.status})",
                    "data": {},
                    "skipped": True,
                    "market_closed": True
                }
        
        logger.info(
            f"Executing overseas order: {order.ticker} @ {order.exchange}, "
            f"action={order.action}, qty={order.estimated_quantity}"
        )
        
        # 해외주식은 지정가 주문 사용 (모의투자 제약)
        # 시장가를 원하면 현재가 기준으로 약간 높은/낮은 가격으로 지정가 주문
        price = str(order.estimated_price)
        
        return self.overseas_trading.order(
            stock_code=order.ticker,
            exchange_code=order.exchange,
            order_type=order.action,
            quantity=order.estimated_quantity,
            price=price,
            order_division="00"  # 지정가
        )
    
