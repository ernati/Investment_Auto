#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Config 값 디버깅 스크립트
"""

import sys
import os
from pathlib import Path

# 스크립트 경로 추가
sys.path.append(str(Path(__file__).parent / 'Scripts'))

from modules.config_loader import PortfolioConfigLoader

def debug_config():
    """설정값 디버깅"""
    try:
        # Config 로더 초기화
        config_loader = PortfolioConfigLoader()
        
        print("=" * 60)
        print("CONFIG DEBUGGING")
        print("=" * 60)
        
        # 기본 설정 확인
        print("\n[BASIC CONFIG]")
        portfolio_id = config_loader.get_basic("portfolio_id")
        print(f"portfolio_id: {portfolio_id}")
        
        target_weights = config_loader.get_basic("target_weights", {})
        print(f"target_weights: {target_weights}")
        
        # 고급 설정 확인
        print("\n[ADVANCED CONFIG - Risk Guardrails]")
        max_turnover = config_loader.get_advanced("risk_guardrails/max_turnover_per_run", "NOT_FOUND")
        print(f"max_turnover_per_run: {max_turnover} (type: {type(max_turnover)})")
        
        max_orders = config_loader.get_advanced("risk_guardrails/max_orders_per_run", "NOT_FOUND")
        print(f"max_orders_per_run: {max_orders}")
        
        max_single_order = config_loader.get_advanced("risk_guardrails/max_single_order_krw", "NOT_FOUND")
        print(f"max_single_order_krw: {max_single_order}")
        
        # 전체 risk_guardrails 확인
        print("\n[FULL RISK_GUARDRAILS]")
        risk_guardrails = config_loader.get_advanced("risk_guardrails", {})
        print(f"risk_guardrails: {risk_guardrails}")
        
        # 설정 파일 경로 확인
        print("\n[CONFIG PATHS]")
        print(f"Config dir: {config_loader.config_dir}")
        print(f"Basic config exists: {config_loader.basic_config_path.exists()}")
        print(f"Advanced config exists: {config_loader.advanced_config_path.exists()}")
        
        # 로드된 설정 확인
        print(f"\nBasic config loaded: {config_loader.basic_config is not None}")
        print(f"Advanced config loaded: {config_loader.advanced_config is not None}")
        
        if config_loader.advanced_config:
            print(f"\nAdvanced config keys: {list(config_loader.advanced_config.keys())}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_config()