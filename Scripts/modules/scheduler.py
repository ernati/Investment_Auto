# -*- coding: utf-8 -*-
"""
Portfolio Scheduler Module
설정 기반 스케줄링: 언제 리밸런싱을 측정하고 실행할지 결정
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
from zoneinfo import ZoneInfo

from .config_loader import PortfolioConfigLoader


logger = logging.getLogger(__name__)


class PortfolioScheduler:
    """포트폴리오 리밸런싱 스케줄을 관리하는 클래스"""
    
    def __init__(self, config_loader: PortfolioConfigLoader):
        """
        Args:
            config_loader (PortfolioConfigLoader): 설정 로더
        """
        self.config = config_loader
        
        # 설정에서 스케줄 정보 로드
        self.timezone_str = self.config.get_basic("rebalance/schedule/timezone", "Asia/Seoul")
        try:
            self.timezone = ZoneInfo(self.timezone_str)
        except Exception as e:
            logger.warning(f"Invalid timezone {self.timezone_str}, using Asia/Seoul: {e}")
            self.timezone = ZoneInfo("Asia/Seoul")
        
        # Hourly 규칙 확인
        self.hourly_enabled = self.config.get_basic("rebalance/schedule/calendar_rules/hourly/enabled", False)
        self.hourly_minute = int(self.config.get_basic("rebalance/schedule/calendar_rules/hourly/minute", 0))
        
        # Run times 확인
        self.run_times: List[str] = self.config.get_basic("rebalance/schedule/run_times", [])
        
        # Calendar rules 확인
        self.month_end = self.config.get_basic("rebalance/schedule/calendar_rules/month_end", False)
        self.quarter_end = self.config.get_basic("rebalance/schedule/calendar_rules/quarter_end", False)
        self.weekly_enabled = self.config.get_basic("rebalance/schedule/calendar_rules/weekly/enabled", False)
        self.weekly_weekday = self.config.get_basic("rebalance/schedule/calendar_rules/weekly/weekday", "FRI")
        
        # 실행 횟수 제한
        self.max_runs_per_day = self.config.get_advanced("run_limit/max_runs_per_day", 999)
        self.last_run_time: Optional[datetime] = None
        self.runs_today = 0
        self.last_reset_date: Optional[datetime] = None
        
        logger.info(
            f"Scheduler initialized: "
            f"timezone={self.timezone_str}, "
            f"hourly_enabled={self.hourly_enabled}, "
            f"max_runs_per_day={self.max_runs_per_day}"
        )
    
    def is_execution_time(self, current_time: Optional[datetime] = None) -> bool:
        """
        현재 시간이 리밸런싱 실행 시간인지 판단합니다.
        
        Args:
            current_time (datetime, optional): 판단할 시간. None이면 현재시간 사용
            
        Returns:
            bool: 실행 시간이면 True
        """
        if current_time is None:
            current_time = datetime.now(self.timezone)
        
        # 일일 실행 횟수 제한 확인
        if self._should_reset_run_count(current_time):
            self.runs_today = 0
            self.last_reset_date = current_time
        
        if self.runs_today >= self.max_runs_per_day:
            logger.warning(
                f"Daily run limit reached: {self.runs_today}/{self.max_runs_per_day}"
            )
            return False
        
        # 스케줄 우선순위: hourly > run_times
        if self.hourly_enabled:
            return self._is_hourly_execution_time(current_time)
        else:
            return self._is_scheduled_execution_time(current_time)
    
    def _is_hourly_execution_time(self, current_time: datetime) -> bool:
        """
        Hourly 규칙에 따른 실행 시간 판단.
        매 시간의 지정된 분(minute)에 실행.
        
        Args:
            current_time (datetime): 판단할 시간
            
        Returns:
            bool: 매 시간의 지정된 분이면 True
        """
        # 현재 분이 지정된 분과 일치하면 True
        is_execution = current_time.minute == self.hourly_minute
        
        if is_execution:
            logger.info(f"Hourly execution time: {current_time.strftime('%H:{:02d}'.format(self.hourly_minute))}")
        
        return is_execution
    
    def _is_scheduled_execution_time(self, current_time: datetime) -> bool:
        """
        Run times 또는 Calendar rules에 따른 실행 시간 판단.
        
        Args:
            current_time (datetime): 판단할 시간
            
        Returns:
            bool: 실행 시간이면 True
        """
        # 1. Run times 확인 (HH:MM 형식)
        if self.run_times:
            current_time_str = current_time.strftime("%H:%M")
            if current_time_str in self.run_times:
                logger.info(f"Scheduled execution time: {current_time_str}")
                return True
        
        # 2. Calendar rules 확인
        if self._is_calendar_rule_match(current_time):
            logger.info(f"Calendar rule match: {current_time}")
            return True
        
        return False
    
    def _is_calendar_rule_match(self, current_time: datetime) -> bool:
        """
        Calendar rules (월말, 분기말, 주간) 확인.
        
        Args:
            current_time (datetime): 판단할 시간
            
        Returns:
            bool: 조건 일치하면 True
        """
        # 월말 확인
        if self.month_end and self._is_month_end(current_time):
            return True
        
        # 분기말 확인
        if self.quarter_end and self._is_quarter_end(current_time):
            return True
        
        # 주간 확인
        if self.weekly_enabled and self._is_target_weekday(current_time):
            return True
        
        return False
    
    @staticmethod
    def _is_month_end(current_time: datetime) -> bool:
        """월말 판단 (다음달 1일 이전)"""
        next_day = current_time + timedelta(days=1)
        return next_day.day == 1
    
    @staticmethod
    def _is_quarter_end(current_time: datetime) -> bool:
        """분기말 판단 (3월, 6월, 9월, 12월 말일)"""
        quarter_end_months = [3, 6, 9, 12]
        next_day = current_time + timedelta(days=1)
        return current_time.month in quarter_end_months and next_day.day == 1
    
    def _is_target_weekday(self, current_time: datetime) -> bool:
        """특정 요일 판단"""
        weekday_map = {
            "MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6
        }
        
        target_weekday = weekday_map.get(self.weekly_weekday, 4)  # 기본: 금요일
        return current_time.weekday() == target_weekday
    
    def _should_reset_run_count(self, current_time: datetime) -> bool:
        """일일 실행 횟수 카운트를 리셋해야 하는지 판단"""
        if self.last_reset_date is None:
            return True
        
        # 날짜가 변경되었으면 리셋
        return current_time.date() != self.last_reset_date.date()
    
    def record_execution(self, execution_time: Optional[datetime] = None) -> None:
        """
        리밸런싱 실행을 기록합니다.
        
        Args:
            execution_time (datetime, optional): 실행 시간. None이면 현재시간 사용
        """
        if execution_time is None:
            execution_time = datetime.now(self.timezone)
        
        self.last_run_time = execution_time
        self.runs_today += 1
        
        logger.info(
            f"Execution recorded: {execution_time.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"runs today: {self.runs_today}/{self.max_runs_per_day}"
        )
    
    def get_next_execution_time(self, current_time: Optional[datetime] = None) -> Optional[datetime]:
        """
        다음 실행 시간을 계산합니다 (근사값).
        
        Args:
            current_time (datetime, optional): 기준 시간. None이면 현재시간 사용
            
        Returns:
            datetime: 다음 실행 예정 시간
        """
        if current_time is None:
            current_time = datetime.now(self.timezone)
        
        if self.hourly_enabled:
            # Hourly: 다음 정각의 지정된 분
            if current_time.minute >= self.hourly_minute:
                # 다음 시간
                next_time = current_time.replace(minute=self.hourly_minute, second=0, microsecond=0)
                next_time += timedelta(hours=1)
            else:
                # 이번 시간
                next_time = current_time.replace(minute=self.hourly_minute, second=0, microsecond=0)
            return next_time
        else:
            # Run times 기반
            if self.run_times:
                # 오늘의 run_times 중에서 다음 시간 찾기
                current_time_str = current_time.strftime("%H:%M")
                future_times = [t for t in sorted(self.run_times) if t > current_time_str]
                
                if future_times:
                    next_run = future_times[0]
                    hour, minute = map(int, next_run.split(':'))
                    return current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    # 내일의 첫 run_time
                    tomorrow = current_time + timedelta(days=1)
                    first_run = sorted(self.run_times)[0]
                    hour, minute = map(int, first_run.split(':'))
                    return tomorrow.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            return None
