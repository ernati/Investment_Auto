# -*- coding: utf-8 -*-
"""
Config Loader Module
JSON 설정 파일을 로드하고 관리하는 모듈
- config_basic.json: 기본 설정 (사용자가 조정)
- config_advanced.json: 고급 설정 (운영/전문가가 조정)
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


def print_config_summary(config: Dict[str, Any], title: str = "설정 정보") -> None:
    """설정 데이터를 읽기 쉽게 출력합니다.
    
    Args:
        config (Dict[str, Any]): 출력할 설정 데이터
        title (str): 출력할 제목
    """
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")
    _print_config_section(config)
    print(f"{'='*60}\n")


def _print_config_section(data: Any, prefix: str = "") -> None:
    """설정 섹션을 재귀적으로 출력하는 내부 함수
    
    Args:
        data: 출력할 데이터 (dict, list, 또는 기본 타입)
        prefix (str): 들여쓰기용 접두사
    """
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                print(f"{prefix}{key}:")
                _print_config_section(value, prefix + "  ")
            else:
                print(f"{prefix}{key}: {value}")
    elif isinstance(data, list):
        if len(data) == 0:
            print(f"{prefix}(빈 리스트)")
        else:
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    print(f"{prefix}[{i}]:")
                    _print_config_section(item, prefix + "  ")
                else:
                    print(f"{prefix}[{i}]: {item}")
    else:
        print(f"{prefix}{data}")


class ConfigLoader:
    """KIS API 설정 파일(config.json)을 로드하고 관리하는 클래스"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Args:
            config_path (Path, optional): 설정 파일 경로. None이면 기본 경로 사용
        """
        if config_path is None:
            current_dir = Path(__file__).parent.parent.parent
            config_path = current_dir / "Config" / "config.json"

        self.config_path = Path(config_path)
        self.config: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        """설정 파일을 로드합니다.

        Returns:
            dict: 설정 데이터

        Raises:
            FileNotFoundError: 설정 파일이 없을 경우
            json.JSONDecodeError: JSON 파싱 오류 시
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"설정 파일을 찾을 수 없습니다: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        logger.info(f"Loaded config from {self.config_path}")
        return self.config

    def get(self, key_path: str, default: Any = None) -> Any:
        """점(.)으로 구분된 키 경로로 설정 값을 가져옵니다."""
        if not self.config:
            self.load()

        keys = key_path.split('.')
        value: Any = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_kis_config(self, env: str = 'real') -> Dict[str, Any]:
        """KIS API 설정을 가져옵니다.

        Args:
            env (str): 환경 ('real' 또는 'demo')

        Returns:
            dict: KIS API 설정

        Raises:
            ValueError: 해당 환경의 설정이 없을 때
        """
        if not self.config:
            self.load()

        kis_config = self.config.get('kis', {}).get(env)
        if not kis_config:
            raise ValueError(f"KIS 설정을 찾을 수 없습니다: env={env}")

        return kis_config
    
    def get_upbit_config(self, env: str = 'real') -> Dict[str, Any]:
        """Upbit API 설정을 가져옵니다.

        Args:
            env (str): 환경 ('real' 또는 'demo')

        Returns:
            dict: Upbit API 설정

        Raises:
            ValueError: 해당 환경의 설정이 없을 때
        """
        if not self.config:
            self.load()

        upbit_config = self.config.get('upbit', {}).get(env)
        if not upbit_config:
            raise ValueError(f"Upbit 설정을 찾을 수 없습니다: env={env}")

        return upbit_config
    
    def print_loaded_config(self) -> None:
        """로드된 설정 정보를 출력합니다."""
        if not self.config:
            print("설정이 로드되지 않았습니다. 먼저 load() 메소드를 실행하세요.")
            return
        
        print_config_summary(self.config, f"KIS API 설정 ({self.config_path.name})")


class PortfolioConfigLoader:
    """포트폴리오 리밸런싱 설정 파일을 로드하고 관리하는 클래스"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Args:
            config_dir (Path, optional): 설정 파일 디렉토리. None이면 기본 경로 사용
        """
        if config_dir is None:
            # 현재 파일 위치에서 프로젝트 루트의 Config 폴더 찾기
            # Scripts/modules -> Scripts -> Investment_Auto
            current_dir = Path(__file__).parent.parent.parent
            config_dir = current_dir / "Config"
        
        self.config_dir = Path(config_dir)
        self.basic_config: Dict[str, Any] = {}
        self.advanced_config: Dict[str, Any] = {}
        self.merged_config: Dict[str, Any] = {}
        
    def load(self):
        """설정 파일을 로드하고 merge합니다.
        
        Returns:
            dict: merged 설정 데이터
            
        Raises:
            FileNotFoundError: 필수 설정 파일이 없을 경우
            json.JSONDecodeError: JSON 파싱 오류 시
        """
        # 1) config_basic.json 로드 (필수)
        basic_path = self.config_dir / "config_basic.json"
        if not basic_path.exists():
            raise FileNotFoundError(f"필수 설정 파일을 찾을 수 없습니다: {basic_path}")
        
        with open(basic_path, 'r', encoding='utf-8') as f:
            self.basic_config = json.load(f)
        logger.info(f"Loaded basic config from {basic_path}")
        
        # 2) config_advanced.json 로드 (선택)
        advanced_path = self.config_dir / "config_advanced.json"
        if advanced_path.exists():
            with open(advanced_path, 'r', encoding='utf-8') as f:
                self.advanced_config = json.load(f)
            logger.info(f"Loaded advanced config from {advanced_path}")
        else:
            logger.warning(f"Advanced config file not found: {advanced_path}")
            self.advanced_config = {}
        
        # 3) Deep merge (advanced가 basic을 override)
        self.merged_config = self._deep_merge(self.basic_config, self.advanced_config)
        logger.info("Config files merged (advanced overrides basic)")
        
        return self.merged_config
    
    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        base 딕셔너리에 override를 deep merge합니다.
        override 값이 우선합니다.
        
        Args:
            base: 기본 딕셔너리
            override: 오버라이드할 딕셔너리
            
        Returns:
            merged 딕셔너리
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = PortfolioConfigLoader._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        중첩된 키 경로로 merged 설정 값을 가져옵니다.
        
        Args:
            key_path (str): 슬래시(/)로 구분된 키 경로 (예: "portfolio_id", "rebalance/mode")
            default: 키가 없을 때 반환할 기본값
            
        Returns:
            설정 값 또는 기본값
        """
        if not self.merged_config:
            self.load()
        
        keys = key_path.split('/')
        value = self.merged_config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_basic(self, key_path: str, default: Any = None) -> Any:
        """
        기본 설정에서만 값을 가져옵니다 (BASIC:/ 참조).
        
        Args:
            key_path (str): 슬래시(/)로 구분된 키 경로
            default: 키가 없을 때 반환할 기본값
            
        Returns:
            설정 값 또는 기본값
        """
        if not self.basic_config:
            self.load()
        
        keys = key_path.split('/')
        value = self.basic_config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_advanced(self, key_path: str, default: Any = None) -> Any:
        """
        고급 설정에서만 값을 가져옵니다 (ADV:/ 참조).
        
        Args:
            key_path (str): 슬래시(/)로 구분된 키 경로
            default: 키가 없을 때 반환할 기본값
            
        Returns:
            설정 값 또는 기본값
        """
        if not self.advanced_config:
            self.load()
        
        keys = key_path.split('/')
        value = self.advanced_config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_merged(self) -> Dict[str, Any]:
        """전체 merged 설정을 반환합니다."""
        if not self.merged_config:
            self.load()
        return self.merged_config
    
    def print_loaded_config(self) -> None:
        """로드된 모든 설정 정보를 출력합니다."""
        if not self.merged_config:
            print("설정이 로드되지 않았습니다. 먼저 load() 메소드를 실행하세요.")
            return
        
        # 기본 설정 출력
        if self.basic_config:
            print_config_summary(
                self.basic_config, 
                f"기본 설정 ({self.config_dir}/config_basic.json)"
            )
        
        # 고급 설정 출력 (있는 경우)
        if self.advanced_config:
            print_config_summary(
                self.advanced_config, 
                f"고급 설정 ({self.config_dir}/config_advanced.json)"
            )
        else:
            print(f"\n{'='*60}")
            print(" 고급 설정 (config_advanced.json)")
            print(f"{'='*60}")
            print("  (파일이 존재하지 않거나 비어있습니다)")
            print(f"{'='*60}\n")
        
        # 병합된 최종 설정 출력
        print_config_summary(self.merged_config, "최종 병합된 설정")
        
        # 설정 적용 요약 출력
        self._print_config_summary()
    
    def _print_config_summary(self) -> None:
        """설정 적용 상태를 요약하여 출력합니다."""
        print(f"\n{'='*60}")
        print(" 설정 적용 요약")
        print(f"{'='*60}")
        
        # 주요 설정값들 체크  
        portfolio_id = self.get("portfolio_id")
        base_currency = self.get("base_currency", "KRW")
        target_weights = self.get("target_weights", {})
        rebalance_mode = self.get("rebalance/mode", "HYBRID")
        
        print(f"포트폴리오 ID: {portfolio_id}")
        print(f"기준 통화: {base_currency}")
        print(f"리밸런싱 모드: {rebalance_mode}")
        
        # 카테고리별 자산 수 계산
        total_assets = 0
        category_counts = {}
        if target_weights:
            for category, assets in target_weights.items():
                if isinstance(assets, dict):
                    count = len(assets)
                    category_counts[category] = count
                    total_assets += count
        
        print(f"총 자산 수: {total_assets}개")
        for category, count in category_counts.items():
            print(f"  {category}: {count}개")
        
        if target_weights:
            print("카테고리별 목표 자산:")
            for category, assets in target_weights.items():
                if isinstance(assets, dict) and assets:
                    print(f"  [{category}]:")
                    category_total = 0.0
                    for ticker, weight in assets.items():
                        print(f"    {ticker}: {weight*100:.1f}%")
                        category_total += weight
                    print(f"    소계: {category_total*100:.1f}%")
        
        # 리밸런싱 설정
        price_source = self.get("rebalance/price_source", "last")
        band_type = self.get("rebalance/band/type", "ABS")
        band_value = self.get("rebalance/band/value", 0.05)
        
        print(f"가격 소스: {price_source}")
        print(f"리밸런싱 밴드: {band_type} {band_value}")
        
        # 거래 설정
        cash_buffer = self.get("trade/cash_buffer_ratio", 0.02)
        min_order_krw = self.get("trade/min_order_krw", 100000)
        
        print(f"현금 버퍼 비율: {cash_buffer*100:.2f}%")
        print(f"최소 주문 금액: {min_order_krw:,}원")
        
        print(f"{'='*60}\n")


# 전역 설정 로더 인스턴스
_global_config: Optional[PortfolioConfigLoader] = None
_global_app_config: Optional[ConfigLoader] = None


def get_config(reload: bool = False) -> ConfigLoader:
    """전역 KIS 설정 로더 인스턴스를 가져옵니다."""
    global _global_app_config

    if _global_app_config is None or reload:
        _global_app_config = ConfigLoader()
        _global_app_config.load()

    return _global_app_config


def get_portfolio_config(reload: bool = False) -> PortfolioConfigLoader:
    """
    전역 포트폴리오 설정 로더 인스턴스를 가져옵니다.
    
    Args:
        reload (bool): 설정을 다시 로드할지 여부
        
    Returns:
        PortfolioConfigLoader: 설정 로더 인스턴스
    """
    global _global_config
    
    if _global_config is None or reload:
        _global_config = PortfolioConfigLoader()
        _global_config.load()
    
    return _global_config
