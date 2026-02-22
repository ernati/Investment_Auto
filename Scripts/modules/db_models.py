# -*- coding: utf-8 -*-
"""
Database Models and Schema Definitions
투자 자동화 시스템의 데이터베이스 스키마 및 모델 정의
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, Any, List, Optional
import json


@dataclass
class TradingHistoryRecord:
    """거래 기록 모델"""
    portfolio_id: str
    symbol: str
    order_type: str  # 'buy', 'sell'
    quantity: float
    price: float
    total_amount: float
    commission: float
    order_id: str
    status: str  # 'completed', 'failed', 'pending'
    environment: str  # 'real', 'demo'
    timestamp: Optional[datetime] = None
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화 가능)"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class RebalancingLogRecord:
    """리밸런싱 로그 모델"""
    portfolio_id: str
    rebalance_reason: str
    target_weights: Dict[str, Any]
    before_weights: Dict[str, Any]
    after_weights: Dict[str, Any]
    orders_executed: int
    status: str  # 'success', 'failed', 'partial'
    environment: str
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화 가능)"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class PortfolioSnapshotRecord:
    """포트폴리오 스냅샷 모델"""
    portfolio_id: str
    total_value: float
    positions: Dict[str, Any]
    environment: str
    timestamp: Optional[datetime] = None
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화 가능)"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class SystemLogRecord:
    """시스템 로그 모델"""
    level: str  # 'INFO', 'ERROR', 'WARNING'
    module: str
    message: str
    environment: str
    extra_data: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화 가능)"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data


# 테이블 생성 SQL 스크립트들
CREATE_TABLES_SQL = {
    'trading_history': """
        CREATE TABLE IF NOT EXISTS trading_history (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            portfolio_id VARCHAR(50) NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            order_type VARCHAR(10) NOT NULL,
            quantity DECIMAL(15,8) NOT NULL,
            price DECIMAL(15,2) NOT NULL,
            total_amount DECIMAL(15,2) NOT NULL,
            commission DECIMAL(15,2) DEFAULT 0,
            order_id VARCHAR(100),
            status VARCHAR(20) NOT NULL,
            environment VARCHAR(10) NOT NULL,
            
            INDEX idx_trading_timestamp (timestamp),
            INDEX idx_trading_portfolio (portfolio_id),
            INDEX idx_trading_symbol (symbol),
            INDEX idx_trading_environment (environment)
        );
    """,
    
    'rebalancing_logs': """
        CREATE TABLE IF NOT EXISTS rebalancing_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            portfolio_id VARCHAR(50) NOT NULL,
            rebalance_reason TEXT NOT NULL,
            target_weights JSON NOT NULL,
            before_weights JSON NOT NULL,
            after_weights JSON NOT NULL,
            orders_executed INTEGER DEFAULT 0,
            status VARCHAR(20) NOT NULL,
            error_message TEXT,
            environment VARCHAR(10) NOT NULL,
            
            INDEX idx_rebalancing_timestamp (timestamp),
            INDEX idx_rebalancing_portfolio (portfolio_id),
            INDEX idx_rebalancing_status (status),
            INDEX idx_rebalancing_environment (environment)
        );
    """,
    
    'portfolio_snapshots': """
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            portfolio_id VARCHAR(50) NOT NULL,
            total_value DECIMAL(15,2) NOT NULL,
            positions JSON NOT NULL,
            environment VARCHAR(10) NOT NULL,
            
            INDEX idx_snapshot_timestamp (timestamp),
            INDEX idx_snapshot_portfolio (portfolio_id),
            INDEX idx_snapshot_environment (environment)
        );
    """,
    
    'system_logs': """
        CREATE TABLE IF NOT EXISTS system_logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            level VARCHAR(20) NOT NULL,
            module VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            extra_data JSON,
            environment VARCHAR(10) NOT NULL,
            
            INDEX idx_system_timestamp (timestamp),
            INDEX idx_system_level (level),
            INDEX idx_system_module (module),
            INDEX idx_system_environment (environment)
        );
    """
}

# 데이터 정리 SQL 스크립트들
CLEANUP_QUERIES = {
    'trading_history': """
        DELETE FROM trading_history 
        WHERE timestamp < NOW() - INTERVAL '{retention_days} days'
        AND environment = %s;
    """,
    
    'rebalancing_logs': """
        DELETE FROM rebalancing_logs 
        WHERE timestamp < NOW() - INTERVAL '{retention_days} days'
        AND environment = %s;
    """,
    
    'portfolio_snapshots': """
        DELETE FROM portfolio_snapshots 
        WHERE timestamp < NOW() - INTERVAL '{retention_days} days'
        AND environment = %s;
    """,
    
    'system_logs': """
        DELETE FROM system_logs 
        WHERE timestamp < NOW() - INTERVAL '{retention_days} days'
        AND environment = %s;
    """
}