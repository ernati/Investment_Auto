# -*- coding: utf-8 -*-
"""
Config Validator Module
설정 파일 검증: 설계서 규칙에 따른 설정 검증
"""

import logging
from typing import Tuple, List

try:
    from .config_loader import PortfolioConfigLoader
except ImportError:
    from config_loader import PortfolioConfigLoader


logger = logging.getLogger(__name__)


class ConfigValidator:
    """포트폴리오 설정 검증 클래스"""
    
    def __init__(self, config_loader: PortfolioConfigLoader):
        """
        Args:
            config_loader (PortfolioConfigLoader): 설정 로더
        """
        self.config = config_loader
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self) -> Tuple[bool, List[str], List[str]]:
        """
        설정을 검증합니다.
        
        Returns:
            (success, errors, warnings)
        """
        self.errors = []
        self.warnings = []
        
        # 필수 설정 검증
        self._validate_required_fields()
        
        # 설정 값 검증
        self._validate_target_weights()
        self._validate_rebalance_settings()
        self._validate_trade_settings()
        self._validate_schedule_settings()
        self._validate_live_mode_settings()
        
        success = len(self.errors) == 0
        
        # 로깅
        if success:
            logger.info("All validations passed")
        else:
            logger.error(f"Validation failed with {len(self.errors)} errors")
        
        if self.warnings:
            logger.warning(f"There are {len(self.warnings)} warnings")
        
        return success, self.errors, self.warnings
    
    def _validate_required_fields(self) -> None:
        """필수 필드를 검증합니다."""
        required_basic = [
            'portfolio_id',
            'base_currency',
            'target_weights',
        ]
        
        for field in required_basic:
            if not self.config.get_basic(field):
                self.errors.append(f"BASIC: Missing required field '{field}'")
    
    def _validate_target_weights(self) -> None:
        """목표 비중을 검증합니다 (카테고리별 구조)."""
        target_weights = self.config.get_basic("target_weights", {})
        
        if not target_weights:
            self.errors.append("BASIC:/target_weights: Must not be empty")
            return
        
        # 카테고리 검증
        if not isinstance(target_weights, dict):
            self.errors.append("BASIC:/target_weights: Must be a dictionary with asset categories")
            return
            
        # 지원되는 자산 카테고리
        supported_categories = ['stocks', 'overseas_stocks', 'bonds', 'etfs', 'reits', 'commodities', 'crypto']
        
        total_weight = 0.0
        category_weights = {}
        
        # 각 카테고리별로 검증
        for category, assets in target_weights.items():
            if category not in supported_categories:
                self.warnings.append(
                    f"BASIC:/target_weights/{category}: Unknown category '{category}'. "
                    f"Supported: {', '.join(supported_categories)}"
                )
            
            if not isinstance(assets, dict):
                self.errors.append(
                    f"BASIC:/target_weights/{category}: Must be a dictionary of assets"
                )
                continue
                
            if not assets:
                self.warnings.append(
                    f"BASIC:/target_weights/{category}: Category is empty"
                )
                continue
            
            category_total = 0.0
            
            # 각 자산별 비중 검증
            for ticker, weight in assets.items():
                # overseas_stocks의 경우 weight가 dict 형태 ({"exchange": "AMEX", "weight": 0.4})
                if isinstance(weight, dict):
                    actual_weight = weight.get("weight", 0)
                    if not isinstance(actual_weight, (int, float)):
                        self.errors.append(
                            f"BASIC:/target_weights/{category}/{ticker}: "
                            f"Weight must be a number, got {type(actual_weight).__name__}"
                        )
                        continue
                    weight = actual_weight
                elif not isinstance(weight, (int, float)):
                    self.errors.append(
                        f"BASIC:/target_weights/{category}/{ticker}: "
                        f"Weight must be a number, got {type(weight).__name__}"
                    )
                    continue
                    
                if not (0 <= weight <= 1):
                    self.errors.append(
                        f"BASIC:/target_weights/{category}/{ticker}: "
                        f"Weight must be between 0 and 1, got {weight}"
                    )
                
                category_total += weight
                total_weight += weight
            
            category_weights[category] = category_total
        
        # 전체 합계가 1.0인지 확인
        if abs(total_weight - 1.0) > 1e-6:
            self.errors.append(
                f"BASIC:/target_weights: Total sum must be 1.0, got {total_weight:.6f}. "
                f"Category breakdown: {category_weights}"
            )
        
        # 카테고리별 비중 정보 로깅
        if category_weights:
            logger.info(f"Asset allocation by category: {category_weights}")
            logger.info(f"Total portfolio weight: {total_weight:.6f}")
    
    def _validate_rebalance_settings(self) -> None:
        """리밸런싱 설정을 검증합니다."""
        mode = self.config.get_basic("rebalance/mode")
        if mode not in ["BAND", "CALENDAR", "HYBRID"]:
            self.errors.append(
                f"BASIC:/rebalance/mode: "
                f"Must be 'BAND', 'CALENDAR', or 'HYBRID', got '{mode}'"
            )
        
        # Band 설정 검증 (BAND 또는 HYBRID 모드일 때)
        if mode in ["BAND", "HYBRID"]:
            band_type = self.config.get_basic("rebalance/band/type")
            if band_type not in ["ABS", "REL"]:
                self.errors.append(
                    f"BASIC:/rebalance/band/type: "
                    f"Must be 'ABS' or 'REL', got '{band_type}'"
                )
            
            band_value = self.config.get_basic("rebalance/band/value")
            if band_value is None or band_value < 0:
                self.errors.append(
                    f"BASIC:/rebalance/band/value: "
                    f"Must be non-negative, got {band_value}"
                )
        
        # Price source 검증
        price_source = self.config.get_basic("rebalance/price_source")
        if price_source not in ["close", "last"]:
            self.errors.append(
                f"BASIC:/rebalance/price_source: "
                f"Must be 'close' or 'last', got '{price_source}'"
            )
    
    def _validate_trade_settings(self) -> None:
        """거래 설정을 검증합니다."""
        # Cash buffer ratio
        cash_buffer = self.config.get_basic("trade/cash_buffer_ratio")
        if not (0 <= cash_buffer <= 1):
            self.errors.append(
                f"BASIC:/trade/cash_buffer_ratio: "
                f"Must be between 0 and 1, got {cash_buffer}"
            )
        
        # Min order KRW
        min_order = self.config.get_basic("trade/min_order_krw")
        if not isinstance(min_order, (int, float)) or min_order < 0:
            self.errors.append(
                f"BASIC:/trade/min_order_krw: "
                f"Must be non-negative integer, got {min_order}"
            )
    
    def _validate_schedule_settings(self) -> None:
        """스케줄 설정을 검증합니다."""
        timezone = self.config.get_basic("rebalance/schedule/timezone")
        if not timezone:
            self.errors.append("BASIC:/rebalance/schedule/timezone: Missing timezone")
        
        # Hourly와 run_times 우선순위 확인
        hourly_enabled = self.config.get_basic(
            "rebalance/schedule/calendar_rules/hourly/enabled", False
        )
        run_times = self.config.get_basic("rebalance/schedule/run_times", [])
        
        if not hourly_enabled and not run_times:
            self.warnings.append(
                "BASIC:/rebalance/schedule: "
                "Both hourly and run_times are disabled/empty. "
                "Rebalancing will never be triggered."
            )
    
    def _validate_live_mode_settings(self) -> None:
        """실전 모드 설정을 검증합니다."""
        dry_run = self.config.get_basic("dry_run", True)
        kis_env = self.config.get_basic("kis/env", "demo")

        if kis_env == "real" and not dry_run:
            # 실전 모드: 브로커 통합 설정 필수
            broker_provider = self.config.get_advanced(
                "integrations/broker/provider"
            )
            if not broker_provider or broker_provider == "YOUR_BROKER_PROVIDER":
                self.errors.append(
                    "ADV:/integrations/broker/provider: "
                    "Must be configured for LIVE mode (dry_run=false)"
                )
            
            account_id = self.config.get_advanced(
                "integrations/broker/account_id"
            )
            if not account_id or account_id == "ACCOUNT-001":
                self.warnings.append(
                    "ADV:/integrations/broker/account_id: "
                    "Verify account_id is correctly configured"
                )
    
    def print_report(self) -> None:
        """검증 결과 리포트를 출력합니다."""
        print("\n" + "="*60)
        print("Configuration Validation Report")
        print("="*60)
        
        if self.errors:
            print(f"\n[ERROR] ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n[WARNING] WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n[OK] All validations passed!")
        
        print("="*60 + "\n")
