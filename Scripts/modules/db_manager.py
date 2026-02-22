# -*- coding: utf-8 -*-
"""
Database Manager Module
데이터베이스 연결 및 관리를 담당하는 모듈
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2 import OperationalError, DatabaseError
    from psycopg2.extras import RealDictCursor
    from psycopg2.errorcodes import UNDEFINED_TABLE
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from .db_models import (
    TradingHistoryRecord, RebalancingLogRecord, 
    PortfolioSnapshotRecord, SystemLogRecord,
    CREATE_TABLES_SQL, CLEANUP_QUERIES
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """데이터베이스 연결 및 관리 클래스"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        데이터베이스 매니저 초기화
        
        Args:
            config_path: 데이터베이스 설정 파일 경로 (기본값: Config/database.json)
        """
        if not PSYCOPG2_AVAILABLE:
            raise ImportError(
                "psycopg2 패키지가 필요합니다. "
                "pip install psycopg2-binary 를 실행해주세요."
            )
        
        # 설정 파일 로드
        if config_path is None:
            config_dir = Path(__file__).parent.parent.parent / "Config"
            config_path = config_dir / "database.json"
        
        self.config = self._load_config(config_path)
        self.db_config = self.config["database"]
        self.table_config = self.config["table_config"]
        self.logging_config = self.config["logging"]
        
        # 로깅 설정
        if self.logging_config.get("enable_query_log", False):
            logging.getLogger("psycopg2").setLevel(logging.DEBUG)
        
        # 초기화 시 테이블 존재 확인 및 생성
        self._initialize_tables()
        
        logger.info(f"Database Manager initialized with config from {config_path}")
    
    def _load_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """설정 파일 로드"""
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Database config file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in database config: {e}")
    
    @contextmanager
    def get_connection(self):
        """
        데이터베이스 연결 컨텍스트 매니저
        자동으로 연결을 닫아줍니다.
        """
        conn = None
        try:
            conn = self._create_connection()
            yield conn
        finally:
            if conn:
                conn.close()
    
    def _create_connection(self):
        """데이터베이스 연결 생성 (재시도 포함)"""
        retry_max = self.db_config.get("retry_max", 3)
        retry_backoff = self.db_config.get("retry_backoff", 0.5)
        
        last_error = None
        for attempt in range(retry_max + 1):
            try:
                conn = psycopg2.connect(
                    host=self.db_config["host"],
                    port=self.db_config["port"],
                    dbname=self.db_config["name"],
                    user=self.db_config["user"],
                    password=self.db_config["password"],
                    sslmode=self.db_config.get("sslmode", "prefer"),
                    connect_timeout=self.db_config.get("connect_timeout", 5),
                    application_name=f"investment-auto/{datetime.now().strftime('%Y%m%d')}"
                )
                logger.debug(f"Database connection successful (attempt {attempt + 1})")
                return conn
            
            except OperationalError as e:
                last_error = e
                logger.warning(
                    f"Database connection failed (attempt {attempt + 1}/{retry_max + 1}): {e}"
                )
                if attempt < retry_max:
                    time.sleep(retry_backoff * (attempt + 1))
        
        logger.error(f"Database connection failed after {retry_max + 1} attempts")
        raise last_error
    
    def test_connection(self) -> bool:
        """데이터베이스 연결 테스트"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    result = cur.fetchone()
                    logger.info("Database connection test successful")
                    return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def create_tables(self) -> bool:
        """모든 테이블 생성"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    for table_name, create_sql in CREATE_TABLES_SQL.items():
                        if self.table_config.get(table_name, {}).get("enabled", True):
                            logger.info(f"Creating table: {table_name}")
                            cur.execute(create_sql)
                    
                    conn.commit()
                    logger.info("All tables created successfully")
                    return True
        
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    def _initialize_tables(self):
        """
        초기화 시 테이블 존재 확인 및 생성
        테이블 생성 실패 시 프로그램 종료
        """
        logger.info("Initializing database tables...")
        
        try:
            if not self.test_connection():
                logger.error("Database connection failed during initialization")
                sys.exit(1)
            
            if not self.create_tables():
                logger.error("Failed to create tables during initialization")
                sys.exit(1)
            
            logger.info("Database tables initialized successfully")
        
        except Exception as e:
            logger.error(f"Critical error during table initialization: {e}")
            sys.exit(1)
    
    def save_trading_history(self, record: TradingHistoryRecord) -> bool:
        """거래 기록 저장"""
        if not self.table_config.get("trading_history", {}).get("enabled", True):
            return True
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO trading_history 
                        (portfolio_id, symbol, order_type, quantity, price, 
                         total_amount, commission, order_id, status, environment)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        record.portfolio_id, record.symbol, record.order_type,
                        record.quantity, record.price, record.total_amount,
                        record.commission, record.order_id, record.status,
                        record.environment
                    ))
                    conn.commit()
                    logger.debug(f"Trading history saved: {record.symbol} {record.order_type}")
                    return True
        
        except DatabaseError as e:
            # 테이블 관련 에러는 프로그램 종료
            if e.pgcode == UNDEFINED_TABLE:
                logger.error(f"Trading history table not found. Database initialization may have failed: {e}")
                sys.exit(1)
            logger.error(f"Database error while saving trading history: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to save trading history: {e}")
            return False
    
    def save_rebalancing_log(self, record: RebalancingLogRecord) -> bool:
        """리밸런싱 로그 저장"""
        if not self.table_config.get("rebalancing_logs", {}).get("enabled", True):
            return True
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO rebalancing_logs 
                        (portfolio_id, rebalance_reason, target_weights, before_weights,
                         after_weights, orders_executed, status, error_message, environment)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        record.portfolio_id, record.rebalance_reason,
                        json.dumps(record.target_weights), json.dumps(record.before_weights),
                        json.dumps(record.after_weights), record.orders_executed,
                        record.status, record.error_message, record.environment
                    ))
                    conn.commit()
                    logger.debug(f"Rebalancing log saved: {record.portfolio_id}")
                    return True
        
        except DatabaseError as e:
            # 테이블 관련 에러는 프로그램 종료
            if e.pgcode == UNDEFINED_TABLE:
                logger.error(f"Rebalancing logs table not found. Database initialization may have failed: {e}")
                sys.exit(1)
            logger.error(f"Database error while saving rebalancing log: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to save rebalancing log: {e}")
            return False
    
    def save_portfolio_snapshot(self, record: PortfolioSnapshotRecord) -> bool:
        """포트폴리오 스냅샷 저장"""
        if not self.table_config.get("portfolio_snapshots", {}).get("enabled", True):
            return True
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO portfolio_snapshots 
                        (portfolio_id, total_value, positions, environment)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        record.portfolio_id, record.total_value,
                        json.dumps(record.positions), record.environment
                    ))
                    conn.commit()
                    logger.debug(f"Portfolio snapshot saved: {record.portfolio_id}")
                    return True
        
        except DatabaseError as e:
            # 테이블 관련 에러는 프로그램 종료
            if e.pgcode == UNDEFINED_TABLE:
                logger.error(f"Portfolio snapshots table not found. Database initialization may have failed: {e}")
                sys.exit(1)
            logger.error(f"Database error while saving portfolio snapshot: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to save portfolio snapshot: {e}")
            return False
    
    def save_system_log(self, record: SystemLogRecord) -> bool:
        """시스템 로그 저장"""
        if not self.table_config.get("system_logs", {}).get("enabled", True):
            return True
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    extra_data_json = json.dumps(record.extra_data) if record.extra_data else None
                    
                    cur.execute("""
                        INSERT INTO system_logs 
                        (level, module, message, extra_data, environment)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        record.level, record.module, record.message,
                        extra_data_json, record.environment
                    ))
                    conn.commit()
                    return True
        
        except DatabaseError as e:
            # 테이블 관련 에러는 프로그램 종료
            if e.pgcode == UNDEFINED_TABLE:
                logger.error(f"System logs table not found. Database initialization may have failed: {e}")
                sys.exit(1)
            logger.error(f"Database error while saving system log: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to save system log: {e}")
            return False
    
    def get_trading_history(self, portfolio_id: str, environment: str, 
                           limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """거래 기록 조회"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM trading_history 
                        WHERE portfolio_id = %s AND environment = %s
                        ORDER BY timestamp DESC
                        LIMIT %s OFFSET %s
                    """, (portfolio_id, environment, limit, offset))
                    
                    return [dict(record) for record in cur.fetchall()]
        
        except Exception as e:
            logger.error(f"Failed to get trading history: {e}")
            return []
    
    def get_rebalancing_logs(self, portfolio_id: str, environment: str,
                           limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """리밸런싱 로그 조회"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM rebalancing_logs 
                        WHERE portfolio_id = %s AND environment = %s
                        ORDER BY timestamp DESC
                        LIMIT %s OFFSET %s
                    """, (portfolio_id, environment, limit, offset))
                    
                    return [dict(record) for record in cur.fetchall()]
        
        except Exception as e:
            logger.error(f"Failed to get rebalancing logs: {e}")
            return []
    
    def get_portfolio_snapshots(self, portfolio_id: str, environment: str,
                              limit: int = 30, offset: int = 0) -> List[Dict[str, Any]]:
        """포트폴리오 스냅샷 조회"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM portfolio_snapshots 
                        WHERE portfolio_id = %s AND environment = %s
                        ORDER BY timestamp DESC
                        LIMIT %s OFFSET %s
                    """, (portfolio_id, environment, limit, offset))
                    
                    return [dict(record) for record in cur.fetchall()]
        
        except Exception as e:
            logger.error(f"Failed to get portfolio snapshots: {e}")
            return []
    
    def cleanup_old_data(self, environment: str) -> Dict[str, int]:
        """오래된 데이터 정리"""
        cleanup_results = {}
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    for table_name, cleanup_sql in CLEANUP_QUERIES.items():
                        if not self.table_config.get(table_name, {}).get("enabled", True):
                            continue
                        
                        retention_days = self.table_config[table_name].get("retention_days", 30)
                        formatted_sql = cleanup_sql.format(retention_days=retention_days)
                        
                        cur.execute(formatted_sql, (environment,))
                        deleted_rows = cur.rowcount
                        cleanup_results[table_name] = deleted_rows
                        
                        logger.info(f"Cleaned up {deleted_rows} rows from {table_name}")
                    
                    conn.commit()
                    logger.info(f"Data cleanup completed: {cleanup_results}")
        
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            cleanup_results["error"] = str(e)
        
        return cleanup_results