# -*- coding: utf-8 -*-
"""
Market Hours Module
한국 주식 시장(KRX) 기준으로 장 상태를 판단하는 유틸리티
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from typing import Optional


@dataclass(frozen=True)
class MarketStatus:
    """시장 상태 정보"""
    status: str
    is_open: bool
    now: datetime
    session_start: datetime
    session_end: datetime
    next_open: datetime


def _next_weekday_open(now: datetime) -> datetime:
    """다음 영업일 09:00 KST를 반환합니다."""
    next_day = now
    while True:
        next_day += timedelta(days=1)
        if next_day.weekday() < 5:
            return next_day.replace(hour=9, minute=0, second=0, microsecond=0)


def get_market_status(
    current_time: Optional[datetime] = None,
    timezone: str = "Asia/Seoul"
) -> MarketStatus:
    """
    KRX 기준 장 상태를 반환합니다.

    Args:
        current_time (datetime, optional): 기준 시간 (None이면 현재 시간)
        timezone (str): 타임존 (기본값: Asia/Seoul)

    Returns:
        MarketStatus: 장 상태 정보
    """
    tz = ZoneInfo(timezone)
    now = current_time.astimezone(tz) if current_time else datetime.now(tz)

    if now.weekday() >= 5:
        next_open = _next_weekday_open(now)
        session_start = next_open
        session_end = next_open.replace(hour=15, minute=30, second=0, microsecond=0)
        return MarketStatus(
            status="closed_weekend",
            is_open=False,
            now=now,
            session_start=session_start,
            session_end=session_end,
            next_open=next_open
        )

    session_start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    session_end = now.replace(hour=15, minute=30, second=0, microsecond=0)

    if now < session_start:
        status = "pre_open"
        next_open = session_start
        is_open = False
    elif now >= session_end:
        status = "after_close"
        next_open = _next_weekday_open(now)
        is_open = False
    else:
        status = "open"
        next_open = now
        is_open = True

    return MarketStatus(
        status=status,
        is_open=is_open,
        now=now,
        session_start=session_start,
        session_end=session_end,
        next_open=next_open
    )


def format_market_status(status: MarketStatus) -> str:
    """시장 상태를 로그용 문자열로 변환합니다."""
    return (
        f"status={status.status}, "
        f"open={status.is_open}, "
        f"now={status.now.strftime('%Y-%m-%d %H:%M:%S')}, "
        f"session={status.session_start.strftime('%H:%M')}-{status.session_end.strftime('%H:%M')}, "
        f"next_open={status.next_open.strftime('%Y-%m-%d %H:%M:%S')}"
    )


# 해외 거래소별 시장 시간 정보
# (timezone, market_open_hour, market_open_minute, market_close_hour, market_close_minute)
OVERSEAS_MARKET_HOURS = {
    # 미국 시장 (NYSE, NASDAQ, AMEX)
    "NYSE": ("America/New_York", 9, 30, 16, 0),
    "NASD": ("America/New_York", 9, 30, 16, 0),
    "AMEX": ("America/New_York", 9, 30, 16, 0),
    # 홍콩 시장
    "SEHK": ("Asia/Hong_Kong", 9, 30, 16, 0),
    # 상해 시장
    "SHAA": ("Asia/Shanghai", 9, 30, 15, 0),
    # 심천 시장
    "SZAA": ("Asia/Shanghai", 9, 30, 15, 0),
    # 도쿄 시장
    "TKSE": ("Asia/Tokyo", 9, 0, 15, 0),
}


def _next_us_weekday_open(now: datetime, tz: ZoneInfo) -> datetime:
    """다음 미국 영업일 09:30 미국 동부 시간을 반환합니다."""
    next_day = now.astimezone(tz)
    while True:
        next_day += timedelta(days=1)
        if next_day.weekday() < 5:
            return next_day.replace(hour=9, minute=30, second=0, microsecond=0)


def get_us_market_status(
    current_time: Optional[datetime] = None,
    exchange_code: str = "AMEX"
) -> MarketStatus:
    """
    미국 시장(NYSE/NASDAQ/AMEX) 기준 장 상태를 반환합니다.
    
    미국 정규장 시간: 09:30 ~ 16:00 (미국 동부 시간, America/New_York)
    
    Args:
        current_time (datetime, optional): 기준 시간 (None이면 현재 시간)
        exchange_code (str): 거래소 코드 (NYSE, NASD, AMEX 등)
        
    Returns:
        MarketStatus: 장 상태 정보
    """
    # 거래소 정보 가져오기 (기본값: 미국 시장)
    market_info = OVERSEAS_MARKET_HOURS.get(exchange_code, OVERSEAS_MARKET_HOURS["AMEX"])
    timezone_str, open_hour, open_minute, close_hour, close_minute = market_info
    
    tz = ZoneInfo(timezone_str)
    now = current_time.astimezone(tz) if current_time else datetime.now(tz)
    
    # 주말 체크
    if now.weekday() >= 5:
        next_open = _next_us_weekday_open(now, tz)
        session_start = next_open
        session_end = next_open.replace(hour=close_hour, minute=close_minute, second=0, microsecond=0)
        return MarketStatus(
            status="closed_weekend",
            is_open=False,
            now=now,
            session_start=session_start,
            session_end=session_end,
            next_open=next_open
        )
    
    session_start = now.replace(hour=open_hour, minute=open_minute, second=0, microsecond=0)
    session_end = now.replace(hour=close_hour, minute=close_minute, second=0, microsecond=0)
    
    if now < session_start:
        status = "pre_open"
        next_open = session_start
        is_open = False
    elif now >= session_end:
        status = "after_close"
        next_open = _next_us_weekday_open(now, tz)
        is_open = False
    else:
        status = "open"
        next_open = now
        is_open = True
    
    return MarketStatus(
        status=status,
        is_open=is_open,
        now=now,
        session_start=session_start,
        session_end=session_end,
        next_open=next_open
    )


def get_overseas_market_status(
    exchange_code: str,
    current_time: Optional[datetime] = None
) -> MarketStatus:
    """
    지정된 해외 거래소의 장 상태를 반환합니다.
    
    Args:
        exchange_code (str): 거래소 코드 (NYSE, NASD, AMEX, SEHK, SHAA, SZAA, TKSE 등)
        current_time (datetime, optional): 기준 시간 (None이면 현재 시간)
        
    Returns:
        MarketStatus: 장 상태 정보
    """
    return get_us_market_status(current_time=current_time, exchange_code=exchange_code)


def is_overseas_market_open(exchange_code: str, current_time: Optional[datetime] = None) -> bool:
    """
    해외 거래소가 현재 열려있는지 확인합니다.
    
    Args:
        exchange_code (str): 거래소 코드 (NYSE, NASD, AMEX, SEHK 등)
        current_time (datetime, optional): 기준 시간 (None이면 현재 시간)
        
    Returns:
        bool: 시장이 열려있으면 True
    """
    status = get_overseas_market_status(exchange_code, current_time)
    return status.is_open
