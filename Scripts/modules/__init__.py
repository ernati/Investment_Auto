# -*- coding: utf-8 -*-
"""
Investment Auto Trading Modules Package
한국투자증권 자동 투자 관련 모듈들
"""

# 기본 모듈들만 import (필요시 추가)
try:
    from .kis_auth import KISAuth
    from .kis_api_utils import build_api_headers, execute_api_request_with_retry
    from .kis_trading import KISTrading
    from .config_loader import PortfolioConfigLoader
    from .config_validator import ConfigValidator
except ImportError as e:
    # 개별 모듈 import 실패 시 경고만 출력
    import warnings
    warnings.warn(f"Some modules could not be imported: {e}")

__version__ = '1.0.0'