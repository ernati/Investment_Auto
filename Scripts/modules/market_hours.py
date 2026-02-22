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
