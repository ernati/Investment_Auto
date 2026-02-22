# -*- coding: utf-8 -*-
"""
KIS App Utils Module
KIS API 애플리케이션 공통 유틸리티 모듈
"""

import sys
from pathlib import Path
from datetime import datetime

# 모듈 경로 추가
sys.path.append(str(Path(__file__).parent))

from .config_loader import get_config
from .kis_auth import KISAuth
from .kis_api_client import KISAPIClient
from .kis_trading import KISTrading


def setup_kis_client(env='real', print_config=True):
    """KIS API 클라이언트를 설정하고 반환합니다.
    
    이 함수는 다음 작업을 수행합니다:
    1. 설정 파일 로드
    2. 설정 정보 출력 (선택사항)
    3. KIS API 인증
    4. API 클라이언트 생성
    
    Args:
        env (str): 환경 ('real' 또는 'demo', 기본값: 'real')
        print_config (bool): 설정 정보를 출력할지 여부 (기본값: True)
        
    Returns:
        tuple: (KISAPIClient, dict) - API 클라이언트와 설정 정보
        
    Raises:
        FileNotFoundError: 설정 파일을 찾을 수 없을 때
        ValueError: KIS 설정이 잘못되었을 때
        Exception: 인증 실패 시
        
    Example:
        >>> client, config = setup_kis_client('demo')
        >>> market_info = client.get_market_price("005930")
    """
    # 1. 설정 로드
    config = get_config()
    config.load()
    kis_config = config.get_kis_config(env)
    
    # 1-1. 설정 정보 출력 (옵션)
    if print_config:
        print(f"\n🔧 KIS API 클라이언트 초기화 - 설정 정보 (환경: {env})")
        print("=" * 70)
        config.print_loaded_config()
    
    # 2. 인증
    auth = KISAuth(
        appkey=kis_config['appkey'],
        appsecret=kis_config['appsecret'],
        account=kis_config['account'],
        product=kis_config['product'],
        htsid=kis_config.get('htsid', ''),
        env=env
    )
    
    auth.authenticate()
    
    # 3. API 클라이언트 생성
    client = KISAPIClient(auth)
    
    return client, kis_config


def setup_kis_trading_client(env='real', print_config=True):
    """KIS API 거래 클라이언트를 설정하고 반환합니다.
    
    이 함수는 다음 작업을 수행합니다:
    1. 설정 파일 로드
    2. 설정 정보 출력 (선택사항)
    3. KIS API 인증
    4. API 클라이언트 및 거래 클라이언트 생성
    
    Args:
        env (str): 환경 ('real' 또는 'demo', 기본값: 'real')
        print_config (bool): 설정 정보를 출력할지 여부 (기본값: True)
        
    Returns:
        tuple: (KISAPIClient, KISTrading, dict) - API 클라이언트, 거래 클라이언트, 설정 정보
        
    Raises:
        FileNotFoundError: 설정 파일을 찾을 수 없을 때
        ValueError: KIS 설정이 잘못되었을 때
        Exception: 인증 실패 시
        
    Example:
        >>> api_client, trading, config = setup_kis_trading_client('demo')
        >>> buy_result = trading.buy_market_order("005930", 1)
    """
    # 1. 설정 로드
    config = get_config()
    config.load()
    kis_config = config.get_kis_config(env)
    
    # 1-1. 설정 정보 출력 (옵션)
    if print_config:
        print(f"\n🔧 KIS API 거래 클라이언트 초기화 - 설정 정보 (환경: {env})")
        print("=" * 70)
        config.print_loaded_config()
    
    # 2. 인증
    auth = KISAuth(
        appkey=kis_config['appkey'],
        appsecret=kis_config['appsecret'],
        account=kis_config['account'],
        product=kis_config['product'],
        htsid=kis_config.get('htsid', ''),
        env=env
    )
    
    auth.authenticate()
    
    # 3. API 클라이언트 및 거래 클라이언트 생성
    api_client = KISAPIClient(auth)
    trading = KISTrading(auth)
    
    return api_client, trading, kis_config


def print_info(message, prefix="[INFO]"):
    """타임스탬프가 포함된 정보 메시지를 출력합니다.
    
    Args:
        message (str): 출력할 메시지
        prefix (str): 메시지 접두어 (기본값: "[INFO]")
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{prefix} {timestamp} - {message}")


def print_header(title, width=60):
    """헤더를 출력합니다.
    
    Args:
        title (str): 제목
        width (int): 출력 너비 (기본값: 60)
    """
    print("=" * width)
    print(title)
    print("=" * width)


def print_separator(width=60, char="-"):
    """구분선을 출력합니다.
    
    Args:
        width (int): 구분선 너비 (기본값: 60)
        char (str): 구분선 문자 (기본값: "-")
    """
    print(char * width)


def format_number(value, unit=""):
    """숫자를 포맷팅합니다.
    
    Args:
        value: 숫자 값 (문자열 또는 숫자)
        unit (str): 단위 (예: "원", "주")
        
    Returns:
        str: 포맷팅된 문자열
    """
    try:
        num = int(value)
        formatted = f"{num:,}"
        if unit:
            formatted += unit
        return formatted
    except (ValueError, TypeError):
        return str(value) + (unit if unit else "")


def print_market_info(market_info, show_details=True):
    """시장가 정보를 포맷팅하여 출력합니다.
    
    Args:
        market_info (dict): 시장가 정보
        show_details (bool): 상세 정보 표시 여부 (기본값: True)
    """
    if not market_info:
        print("시장가 정보를 가져올 수 없습니다.")
        return
    
    print_header("조회 결과")
    
    # 기본 정보
    print(f"\n종목코드: {market_info['종목코드']}")
    print(f"종목명: {market_info['종목명']}")
    
    if show_details:
        # 현재가 및 등락 정보
        print_separator()
        print(f"현재가: {format_number(market_info['현재가'], '원')}")
        print(f"전일대비: {market_info['전일대비']}원 ({market_info['등락률']}%)")
        
        # 가격 정보
        print_separator()
        print(f"시가: {format_number(market_info['시가'], '원')}")
        print(f"고가: {format_number(market_info['고가'], '원')}")
        print(f"저가: {format_number(market_info['저가'], '원')}")
        
        # 거래 정보
        print_separator()
        print(f"거래량: {format_number(market_info['거래량'], '주')}")
        print(f"거래대금: {format_number(market_info['거래대금'], '원')}")
    
    print("=" * 60)


def handle_common_errors(func):
    """공통 에러 처리 데코레이터
    
    Args:
        func: 래핑할 함수
        
    Returns:
        function: 래핑된 함수
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            print(f"\n오류: {e}")
            print("\n설정 파일(Config/config.json)을 확인해주세요.")
            print("APPKEY, APPSECRET, 계좌번호 등을 올바르게 설정했는지 확인하세요.")
        except ValueError as e:
            print(f"\n오류: {e}")
        except Exception as e:
            print(f"\n예상치 못한 오류 발생: {e}")
            import traceback
            traceback.print_exc()
    
    return wrapper


class ProgressPrinter:
    """진행 상황 출력 헬퍼 클래스"""
    
    def __init__(self, title="처리 진행"):
        """
        Args:
            title (str): 진행 상황 제목
        """
        self.title = title
        self.step = 0
    
    def print_step(self, message):
        """단계별 진행 상황을 출력합니다.
        
        Args:
            message (str): 출력할 메시지
        """
        self.step += 1
        print(f"\n[{self.step}] {message}")
    
    def print_sub_step(self, message):
        """하위 단계 정보를 출력합니다.
        
        Args:
            message (str): 출력할 메시지
        """
        print(f"   - {message}")
