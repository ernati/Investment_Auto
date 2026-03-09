# -*- coding: utf-8 -*-
"""
Portfolio Rebalancing Engine Module
리밸런싱 로직: 현재 포트폴리오를 분석하고 주문 계획을 생성
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from .config_loader import PortfolioConfigLoader
from .portfolio_models import (
    PortfolioSnapshot, RebalanceOrder, RebalancePlan
)


logger = logging.getLogger(__name__)


class RebalancingEngine:
    """포트폴리오 리밸런싱 엔진"""
    
    def __init__(self, config_loader: PortfolioConfigLoader):
        """
        Args:
            config_loader (PortfolioConfigLoader): 설정 로더
        """
        self.config = config_loader
        
        # 기본 설정 로드
        self.portfolio_id = self.config.get_basic("portfolio_id")
        self.target_weights_nested = self.config.get_basic("target_weights", {})  # 중첩된 원본
        self.target_weights = self._flatten_target_weights()  # 평면화된 버전
        self.rebalance_mode = self.config.get_basic("rebalance/mode", "HYBRID")
        self.cash_buffer_ratio = self.config.get_basic("trade/cash_buffer_ratio", 0.02)
        self.min_order_krw = self.config.get_basic("trade/min_order_krw", 100000)
        
        # Band 설정 로드
        self.band_type = self.config.get_basic("rebalance/band/type", "ABS")
        self.band_value = float(self.config.get_basic("rebalance/band/value", 0.05))
        
        logger.info(
            f"RebalancingEngine initialized: "
            f"mode={self.rebalance_mode}, "
            f"band_type={self.band_type}, "
            f"band_value={self.band_value}"
        )
    
    def _flatten_target_weights(self) -> dict:
        """
        중첩된 target_weights 구조를 평면적인 딕셔너리로 변환합니다.
        
        Returns:
            dict: {ticker: weight} 형태의 평면적인 딕셔너리
        """
        flattened = {}
        
        for category, assets in self.target_weights_nested.items():
            if isinstance(assets, dict):
                for ticker, weight in assets.items():
                    flattened[ticker] = weight
                    
        logger.debug(f"Flattened target weights: {flattened}")
        return flattened
    
    def create_rebalance_plan(
        self,
        portfolio_snapshot: PortfolioSnapshot,
        is_calendar_triggered: bool = False
    ) -> RebalancePlan:
        """
        포트폴리오 현황을 분석하여 리밸런싱 계획을 생성합니다.
        
        Args:
            portfolio_snapshot (PortfolioSnapshot): 현재 포트폴리오 스냅샷
            is_calendar_triggered (bool): 캘린더 규칙으로 실행되었는지 여부
            
        Returns:
            RebalancePlan: 리밸런싱 계획
        """
        plan = RebalancePlan(
            portfolio_id=self.portfolio_id,
            timestamp=datetime.now(),
            portfolio_snapshot=portfolio_snapshot
        )
        
        # 1. 리밸런싱 필요 여부 판단
        should_rebalance, reason = self._should_rebalance(
            portfolio_snapshot, is_calendar_triggered
        )
        plan.should_rebalance = should_rebalance
        plan.rebalance_reason = reason
        
        if not should_rebalance:
            logger.info(f"Rebalancing not needed: {reason}")
            return plan
        
        logger.info(f"Rebalancing triggered: {reason}")
        
        # 2. 주문 계획 생성
        orders = self._create_orders(portfolio_snapshot)
        plan.orders = orders
        plan.total_orders = len(orders)
        plan.total_delta_value = sum(abs(o.delta_value) for o in orders)
        
        logger.info(f"Created {plan.total_orders} rebalancing orders")
        
        return plan
    
    def _should_rebalance(
        self,
        portfolio_snapshot: PortfolioSnapshot,
        is_calendar_triggered: bool
    ) -> tuple[bool, str]:
        """
        리밸런싱이 필요한지 판단합니다.
        
        Mode별 동작:
        - BAND: 밴드 이탈 시에만 실행
        - CALENDAR: 캘린더 규칙에 의해 실행될 때만 실행
        - HYBRID: BAND 또는 CALENDAR 조건 중 하나라도 만족하면 실행
        
        Returns:
            (should_rebalance, reason): (실행 여부, 이유)
        """
        band_breach = self._has_band_breach(portfolio_snapshot)
        
        if self.rebalance_mode == "BAND":
            return band_breach, "BAND breach detected" if band_breach else "No band breach"
        
        elif self.rebalance_mode == "CALENDAR":
            return is_calendar_triggered, "Calendar triggered" if is_calendar_triggered else "Not calendar time"
        
        elif self.rebalance_mode == "HYBRID":
            if band_breach or is_calendar_triggered:
                reason = ""
                if band_breach:
                    reason += "Band breach; "
                if is_calendar_triggered:
                    reason += "Calendar triggered; "
                return True, reason.rstrip("; ")
            else:
                return False, "No band breach and not calendar time"
        
        else:
            logger.warning(f"Unknown rebalance mode: {self.rebalance_mode}")
            return False, f"Unknown mode: {self.rebalance_mode}"
    
    def _has_band_breach(self, portfolio_snapshot: PortfolioSnapshot) -> bool:
        """
        현재 포트폴리오의 비중이 밴드를 벗어났는지 확인합니다.
        
        Args:
            portfolio_snapshot (PortfolioSnapshot): 포트폴리오 스냅샷
            
        Returns:
            bool: 밴드 이탈하면 True
        """
        current_weights = portfolio_snapshot.get_current_weights()
        
        for ticker, target_weight in self.target_weights.items():
            current_weight = current_weights.get(ticker, 0)
            
            # 밴드 계산
            if self.band_type == "ABS":
                # 절대값 밴드
                lower = target_weight - self.band_value
                upper = target_weight + self.band_value
            else:
                # 상대값 밴드 (비율)
                lower = target_weight * (1 - self.band_value)
                upper = target_weight * (1 + self.band_value)
            
            # 밴드 이탈 확인
            if current_weight < lower or current_weight > upper:
                logger.debug(
                    f"Band breach detected for {ticker}: "
                    f"current={current_weight:.4f}, "
                    f"target={target_weight:.4f}, "
                    f"band=[{lower:.4f}, {upper:.4f}]"
                )
                return True
        
        return False
    
    def _create_orders(self, portfolio_snapshot: PortfolioSnapshot) -> List[RebalanceOrder]:
        """
        주문 계획을 생성합니다.
        비트코인(coin 카테고리)과 주식/채권을 모두 처리합니다.
        
        Args:
            portfolio_snapshot (PortfolioSnapshot): 포트폴리오 스냅샷
            
        Returns:
            List[RebalanceOrder]: 주문 목록
        """
        orders = []
        
        # 코인 티커 상수
        BITCOIN_TICKER = "bitcoin"
        
        # 1. 사용 가능한 자산 계산
        usable_total = (
            portfolio_snapshot.total_value * (1 - self.cash_buffer_ratio)
        )
        
        logger.info(
            f"Creating orders: "
            f"total_value={portfolio_snapshot.total_value:.2f}, "
            f"usable_total={usable_total:.2f} "
            f"(buffer_ratio={self.cash_buffer_ratio:.2%})"
        )
        
        # 2. 각 종목별 주문 생성
        current_weights = portfolio_snapshot.get_current_weights()
        
        for ticker, target_weight in self.target_weights.items():
            target_value = usable_total * target_weight
            current_value = portfolio_snapshot.positions.get(ticker, None)
            current_value = current_value.evaluation if current_value else 0
            current_weight = current_weights.get(ticker, 0)
            
            delta_value = target_value - current_value
            delta_weight = target_weight - current_weight
            
            # 주문이 min_order_krw 미만이면 스킵
            if abs(delta_value) < self.min_order_krw:
                logger.debug(
                    f"Order skipped for {ticker}: "
                    f"delta_value={abs(delta_value):.2f} < min_order_krw={self.min_order_krw}"
                )
                continue
            
            action = "buy" if delta_value > 0 else "sell"
            
            position = portfolio_snapshot.positions.get(
                ticker,
                PositionSnapshot(ticker, 0, 0)
            )
            price = position.price

            # 비트코인 처리 (금액 기반 주문)
            if ticker == BITCOIN_TICKER:
                if price <= 0:
                    logger.warning(
                        f"Skipping BTC order: missing price (price={price})"
                    )
                    continue
                
                # 비트코인은 수량 대신 금액으로 주문
                # estimated_quantity는 1로 설정 (실제 주문은 금액 기반)
                order = RebalanceOrder(
                    ticker=ticker,
                    action=action,
                    target_value=target_value,
                    current_value=current_value,
                    delta_value=delta_value,
                    delta_weight=delta_weight,
                    estimated_quantity=1,  # 비트코인은 금액 기반
                    estimated_price=price
                )
                
                orders.append(order)
                
                logger.info(
                    f"BTC order created: "
                    f"action={action}, "
                    f"delta_value={delta_value:,.0f} KRW, "
                    f"current_weight={current_weight:.4f} -> target_weight={target_weight:.4f}"
                )
                continue

            # 주식/채권 처리 (수량 기반 주문)
            if price <= 0:
                logger.warning(
                    f"Skipping order for {ticker}: missing price (price={price})"
                )
                continue

            estimated_quantity = int(abs(delta_value) / price)
            if estimated_quantity <= 0:
                logger.warning(
                    f"Skipping order for {ticker}: quantity=0 (delta_value={delta_value:.2f}, price={price:.2f})"
                )
                continue

            order = RebalanceOrder(
                ticker=ticker,
                action=action,
                target_value=target_value,
                current_value=current_value,
                delta_value=delta_value,
                delta_weight=delta_weight,
                estimated_quantity=estimated_quantity,
                estimated_price=price
            )
            
            orders.append(order)
            
            logger.debug(
                f"Order created for {ticker}: "
                f"action={action}, "
                f"delta_value={delta_value:.2f}, "
                f"current_weight={current_weight:.4f} -> target_weight={target_weight:.4f}"
            )
        
        return orders
    
    def check_guardrails(self, plan: RebalancePlan) -> tuple[bool, str]:
        """
        리밸런싱 계획이 위험 가드레일을 통과하는지 확인합니다.
        (하위 호환성을 위해 유지, apply_guardrails 사용 권장)
        
        Args:
            plan (RebalancePlan): 리밸런싱 계획
            
        Returns:
            (passed, message): (통과 여부, 메시지)
        """
        # apply_guardrails를 호출하고)결과 확인
        adjusted_plan, message = self.apply_guardrails(plan)
        
        # 원본과 동일하면 통과, 조정되었으면 부분 통과로 간주
        if adjusted_plan.total_orders == plan.total_orders:
            if adjusted_plan.total_delta_value == plan.total_delta_value:
                return True, message
        
        # 조정이 발생했으면 True 반환 (점진적 실행 가능)
        return True, message
    
    def apply_guardrails(self, plan: RebalancePlan) -> tuple[RebalancePlan, str]:
        """
        가드레일을 적용하여 주문을 조정합니다.
        가드레일 초과 시 스킵하는 대신, 한도 내에서 점진적으로 거래합니다.
        
        Args:
            plan (RebalancePlan): 원본 리밸런싱 계획
            
        Returns:
            (adjusted_plan, message): (조정된 계획, 메시지)
        """
        import copy
        
        # 고급 설정에서 가드레일 정보 로드
        max_turnover = self.config.get_advanced("risk_guardrails/max_turnover_per_run", None)
        max_orders = self.config.get_advanced("risk_guardrails/max_orders_per_run", None)
        max_single_order = self.config.get_advanced("risk_guardrails/max_single_order_krw", None)
        
        # 가드레일 없으면 원본 반환
        if not any([max_turnover, max_orders, max_single_order]):
            logger.info("No guardrails configured, passing all orders")
            return plan, "No guardrails"
        
        # 조정된 계획 생성 (깊은 복사)
        adjusted_plan = RebalancePlan(
            portfolio_id=plan.portfolio_id,
            timestamp=plan.timestamp,
            portfolio_snapshot=plan.portfolio_snapshot,
            should_rebalance=plan.should_rebalance,
            rebalance_reason=plan.rebalance_reason
        )
        
        # 주문 복사 (조정용)
        adjusted_orders = []
        for order in plan.orders:
            adjusted_orders.append(RebalanceOrder(
                ticker=order.ticker,
                action=order.action,
                target_value=order.target_value,
                current_value=order.current_value,
                delta_value=order.delta_value,
                delta_weight=order.delta_weight,
                estimated_quantity=order.estimated_quantity,
                estimated_price=order.estimated_price
            ))
        
        messages = []
        
        # 1. 단일 주문 금액 조정 (max_single_order_krw)
        if max_single_order is not None:
            for order in adjusted_orders:
                original_delta = abs(order.delta_value)
                if original_delta > max_single_order:
                    # 한도 내로 조정
                    scale_factor = max_single_order / original_delta
                    new_quantity = int(order.estimated_quantity * scale_factor)
                    
                    if new_quantity > 0:
                        old_qty = order.estimated_quantity
                        order.estimated_quantity = new_quantity
                        # delta_value도 재계산
                        order.delta_value = (
                            new_quantity * order.estimated_price 
                            if order.action == "buy" 
                            else -new_quantity * order.estimated_price
                        )
                        
                        logger.info(
                            f"[Guardrail] {order.ticker}: 단일 주문 한도 적용 "
                            f"({old_qty}주 → {new_quantity}주, "
                            f"금액: {original_delta:,.0f}원 → {abs(order.delta_value):,.0f}원)"
                        )
                        messages.append(
                            f"{order.ticker}: 단일주문한도({max_single_order:,.0f}원) 적용"
                        )
        
        # min_order_krw 미만인 주문 제거
        adjusted_orders = [
            o for o in adjusted_orders 
            if o.estimated_quantity > 0 and abs(o.delta_value) >= self.min_order_krw
        ]
        
        # 2. 주문 개수 조정 (max_orders_per_run)
        if max_orders is not None and len(adjusted_orders) > max_orders:
            original_count = len(adjusted_orders)
            # delta_value의 절대값이 큰 순서로 정렬하여 우선순위 부여
            adjusted_orders.sort(key=lambda o: abs(o.delta_value), reverse=True)
            adjusted_orders = adjusted_orders[:max_orders]
            
            logger.info(
                f"[Guardrail] 주문 개수 한도 적용: {original_count}개 → {max_orders}개 "
                f"(가장 큰 delta 기준으로 선택)"
            )
            messages.append(f"주문개수한도({max_orders}개) 적용: {original_count}→{max_orders}")
        
        # 3. Turnover 조정 (max_turnover_per_run)
        if max_turnover is not None and adjusted_orders:
            portfolio_value = plan.portfolio_snapshot.total_value
            if portfolio_value > 0:
                current_turnover = sum(abs(o.delta_value) for o in adjusted_orders) / portfolio_value
                
                if current_turnover > max_turnover:
                    # 비례적으로 모든 주문 축소
                    scale_factor = max_turnover / current_turnover
                    
                    logger.info(
                        f"[Guardrail] Turnover 한도 적용: {current_turnover:.2%} → {max_turnover:.2%} "
                        f"(scale: {scale_factor:.2%})"
                    )
                    
                    for order in adjusted_orders:
                        old_qty = order.estimated_quantity
                        new_quantity = int(order.estimated_quantity * scale_factor)
                        
                        if new_quantity > 0:
                            order.estimated_quantity = new_quantity
                            order.delta_value = (
                                new_quantity * order.estimated_price 
                                if order.action == "buy" 
                                else -new_quantity * order.estimated_price
                            )
                    
                    messages.append(f"Turnover한도({max_turnover:.0%}) 적용")
        
        # min_order_krw 미만인 주문 다시 제거 (turnover 조정 후)
        adjusted_orders = [
            o for o in adjusted_orders 
            if o.estimated_quantity > 0 and abs(o.delta_value) >= self.min_order_krw
        ]
        
        # 조정된 계획 완성
        adjusted_plan.orders = adjusted_orders
        adjusted_plan.total_orders = len(adjusted_orders)
        adjusted_plan.total_delta_value = sum(abs(o.delta_value) for o in adjusted_orders)
        
        # 결과 메시지 생성
        if messages:
            final_message = "Guardrails applied: " + "; ".join(messages)
            logger.info(final_message)
        else:
            final_message = "All guardrails passed (no adjustment needed)"
            logger.info(final_message)
        
        # 원본 대비 변화 로깅
        if plan.total_orders != adjusted_plan.total_orders or plan.total_delta_value != adjusted_plan.total_delta_value:
            logger.info(
                f"[Guardrail Summary] "
                f"주문수: {plan.total_orders} → {adjusted_plan.total_orders}, "
                f"총거래금액: {plan.total_delta_value:,.0f}원 → {adjusted_plan.total_delta_value:,.0f}원"
            )
        
        return adjusted_plan, final_message


# Import after class definition to avoid circular imports
from .portfolio_models import PositionSnapshot
