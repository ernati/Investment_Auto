# -*- coding: utf-8 -*-
"""
데이터베이스 연결 및 데이터 확인 전용 테스트 스크립트
kis_debug.py의 DB 테스트 부분만 분리한 간단한 버전
"""

import sys
import logging
from pathlib import Path

# Scripts 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.db_manager import DatabaseManager
from modules.db_models import TradingHistoryRecord, SystemLogRecord

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """데이터베이스 전용 테스트 실행"""
    print("🗃️ 데이터베이스 연결 및 데이터 확인 테스트")
    print("=" * 60)
    
    try:
        # DatabaseManager 초기화 (자동 테이블 생성)
        print("📡 데이터베이스 연결 중...")
        db_manager = DatabaseManager()
        print("✅ 데이터베이스 연결 성공")
        
        print("\n📋 테이블별 데이터 현황:")
        
        # 1. 거래 기록 조회
        try:
            trading_data = db_manager.get_trading_history("demo_portfolio", "demo", limit=5)
            count = len(trading_data)
            print(f"  📈 거래 기록: {count}건")
            
            if count > 0:
                print("     최근 3건:")
                for i, trade in enumerate(trading_data[:3], 1):
                    symbol = trade.get('symbol', 'N/A')
                    order_type = trade.get('order_type', 'N/A')
                    quantity = trade.get('quantity', 0)
                    price = trade.get('price', 0)
                    timestamp = str(trade.get('timestamp', 'N/A'))[:19]
                    print(f"       {i}. {timestamp} | {symbol} {order_type} {quantity}주 @ {price:,}원")
            else:
                print("     ⚠️ 데이터 없음 (정상 - 거래 기록이 아직 없음)")
                
        except Exception as e:
            print(f"     ❌ 거래 기록 조회 실패: {e}")
        
        # 2. 리밸런싱 로그 조회
        try:
            rebalancing_data = db_manager.get_rebalancing_logs("demo_portfolio", "demo", limit=3)
            count = len(rebalancing_data)
            print(f"  ⚖️ 리밸런싱 로그: {count}건")
            
            if count > 0:
                print("     최근 2건:")
                for i, log in enumerate(rebalancing_data[:2], 1):
                    reason = str(log.get('rebalance_reason', 'N/A'))[:30]
                    status = log.get('status', 'N/A')
                    orders = log.get('orders_executed', 0)
                    timestamp = str(log.get('timestamp', 'N/A'))[:19]
                    print(f"       {i}. {timestamp} | {status} | {orders}건 | {reason}...")
            else:
                print("     ⚠️ 데이터 없음 (정상 - 리밸런싱 실행 기록이 없음)")
                
        except Exception as e:
            print(f"     ❌ 리밸런싱 로그 조회 실패: {e}")
        
        # 3. 포트폴리오 스냅샷 조회
        try:
            snapshot_data = db_manager.get_portfolio_snapshots("demo_portfolio", "demo", limit=3)
            count = len(snapshot_data)
            print(f"  📸 포트폴리오 스냅샷: {count}건")
            
            if count > 0:
                print("     최근 2건:")
                for i, snapshot in enumerate(snapshot_data[:2], 1):
                    total_value = snapshot.get('total_value', 0)
                    timestamp = str(snapshot.get('timestamp', 'N/A'))[:19]
                    positions = snapshot.get('positions', {})
                    if isinstance(positions, dict):
                        position_count = len(positions)
                    else:
                        position_count = 0
                    print(f"       {i}. {timestamp} | 총자산: {total_value:,.0f}원 | 포지션: {position_count}개")
            else:
                print("     ⚠️ 데이터 없음 (정상 - 포트폴리오 스냅샷이 없음)")
                
        except Exception as e:
            print(f"     ❌ 포트폴리오 스냅샷 조회 실패: {e}")
        
        # 4. 테스트 데이터 생성
        print("\n🧪 테스트 데이터 생성:")
        
        try:
            # 샘플 거래 기록
            sample_trade = TradingHistoryRecord(
                portfolio_id="test_db_check",
                symbol="TEST001", 
                order_type="buy",
                quantity=1.0,
                price=1000.0,
                total_amount=1000.0,
                commission=10.0,
                order_id="TEST_DB_CHECK_001",
                status="completed",
                environment="demo"
            )
            
            if db_manager.save_trading_history(sample_trade):
                print("  ✅ 샘플 거래 기록 저장 성공")
            else:
                print("  ❌ 샘플 거래 기록 저장 실패")
                
        except Exception as e:
            print(f"  ❌ 테스트 데이터 생성 실패: {e}")
        
        try:
            # 샘플 시스템 로그
            sample_log = SystemLogRecord(
                level="INFO",
                module="db_test",
                message="DB 연결 테스트 완료",
                environment="demo",
                extra_data={"test_success": True, "tables_checked": 4}
            )
            
            if db_manager.save_system_log(sample_log):
                print("  ✅ 샘플 시스템 로그 저장 성공")
            else:
                print("  ❌ 샘플 시스템 로그 저장 실패")
                
        except Exception as e:
            print(f"  ❌ 시스템 로그 생성 실패: {e}")
        
        print("\n✅ 데이터베이스 테스트 완료!")
        print("ℹ️ 데이터가 없는 것은 정상입니다 (시스템이 아직 거래를 수행하지 않음)")
        
        return True
        
    except SystemExit:
        print("❌ 데이터베이스 초기화 실패")
        print("💡 확인사항:")
        print("   - PostgreSQL 서비스가 실행 중인가요?")
        print("   - Config/database.json 설정이 올바른가요?")
        print("   - 데이터베이스 사용자 권한이 있나요?")
        return False
        
    except Exception as e:
        print(f"❌ 테스트 실행 실패: {e}")
        print("💡 로그를 확인하고 설정을 점검해보세요.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)