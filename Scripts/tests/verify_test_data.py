# -*- coding: utf-8 -*-
"""
DB 테스트 데이터 검증 스크립트
insert_test_data.py로 삽입된 데이터가 제대로 들어가 있는지 확인
"""

import sys
import logging
from pathlib import Path
import json

# Scripts 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.db_manager import DatabaseManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def verify_trading_history(db_manager: DatabaseManager) -> bool:
    """거래 기록 데이터 검증"""
    print("📈 거래 기록 데이터 확인...")
    
    try:
        data = db_manager.get_trading_history("demo_portfolio", "demo", limit=50)
        print(f"  ✅ 총 {len(data)}건의 거래 기록 발견")
        
        if data:
            print("  📊 최근 거래 기록 (최대 5건):")
            for i, record in enumerate(data[:5]):
                print(f"    {i+1}. [{record['timestamp']}] {record['symbol']} {record['order_type']} "
                      f"{record['quantity']}주 @ {record['price']:,}원 - {record['status']}")
            
            # 주문 유형별 통계
            buy_count = sum(1 for r in data if r['order_type'] == 'buy')
            sell_count = sum(1 for r in data if r['order_type'] == 'sell')
            completed_count = sum(1 for r in data if r['status'] == 'completed')
            
            print(f"  📋 통계: 매수 {buy_count}건, 매도 {sell_count}건, 완료 {completed_count}건")
        else:
            print("  ⚠️ 거래 기록이 없습니다.")
        
        return len(data) > 0
        
    except Exception as e:
        print(f"  ❌ 거래 기록 확인 실패: {e}")
        return False


def verify_rebalancing_logs(db_manager: DatabaseManager) -> bool:
    """리밸런싱 로그 데이터 검증"""
    print("⚖️ 리밸런싱 로그 데이터 확인...")
    
    try:
        data = db_manager.get_rebalancing_logs("demo_portfolio", "demo", limit=30)
        print(f"  ✅ 총 {len(data)}건의 리밸런싱 로그 발견")
        
        if data:
            print("  📊 리밸런싱 로그:")
            for i, record in enumerate(data):
                print(f"    {i+1}. [{record['timestamp']}] {record['status']} - "
                      f"{record['orders_executed']}건 실행")
                print(f"       사유: {record['rebalance_reason'][:50]}...")
                
                # JSON 데이터 파싱
                target_weights = json.loads(record['target_weights']) if isinstance(record['target_weights'], str) else record['target_weights']
                print(f"       목표 비중: {target_weights}")
        else:
            print("  ⚠️ 리밸런싱 로그가 없습니다.")
        
        return len(data) > 0
        
    except Exception as e:
        print(f"  ❌ 리밸런싱 로그 확인 실패: {e}")
        return False


def verify_portfolio_snapshots(db_manager: DatabaseManager) -> bool:
    """포트폴리오 스냅샷 데이터 검증"""
    print("📸 포트폴리오 스냅샷 데이터 확인...")
    
    try:
        data = db_manager.get_portfolio_snapshots("demo_portfolio", "demo", limit=30)
        print(f"  ✅ 총 {len(data)}건의 포트폴리오 스냅샷 발견")
        
        if data:
            print("  📊 포트폴리오 스냅샷:")
            for i, record in enumerate(data[:5]):  # 최대 5개만 표시
                positions = json.loads(record['positions']) if isinstance(record['positions'], str) else record['positions']
                print(f"    {i+1}. [{record['timestamp']}] 총자산: {record['total_value']:,.0f}원")
                print(f"       포지션: {list(positions.keys())}")
        else:
            print("  ⚠️ 포트폴리오 스냅샷이 없습니다.")
        
        return len(data) > 0
        
    except Exception as e:
        print(f"  ❌ 포트폴리오 스냅샷 확인 실패: {e}")
        return False


def verify_system_logs(db_manager: DatabaseManager) -> bool:
    """시스템 로그 데이터 검증"""
    print("📋 시스템 로그 데이터 확인...")
    
    try:
        # system_logs는 db_manager에 직접 메서드가 없으므로 SQL로 직접 조회
        with db_manager.get_connection() as conn:
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM system_logs 
                    WHERE environment = %s
                    ORDER BY timestamp DESC
                    LIMIT 50
                """, ("demo",))
                
                data = [dict(record) for record in cur.fetchall()]
        
        print(f"  ✅ 총 {len(data)}건의 시스템 로그 발견")
        
        if data:
            print("  📊 최근 시스템 로그 (최대 5건):")
            for i, record in enumerate(data[:5]):
                print(f"    {i+1}. [{record['timestamp']}] {record['level']} - {record['module']}")
                print(f"       메시지: {record['message'][:60]}...")
            
            # 레벨별 통계
            levels = {}
            for r in data:
                levels[r['level']] = levels.get(r['level'], 0) + 1
            
            print(f"  📋 레벨별 통계: {levels}")
        else:
            print("  ⚠️ 시스템 로그가 없습니다.")
        
        return len(data) > 0
        
    except Exception as e:
        print(f"  ❌ 시스템 로그 확인 실패: {e}")
        return False


def main():
    """테스트 데이터 검증 메인 함수"""
    print("🔍 DB 테스트 데이터 검증 시작")
    print("=" * 60)
    
    try:
        # DatabaseManager 초기화
        print("📡 데이터베이스 연결 중...")
        db_manager = DatabaseManager()
        print("✅ 데이터베이스 연결 성공")
        print()
        
        # 각 테이블별 데이터 검증
        results = {
            "trading_history": verify_trading_history(db_manager),
            "rebalancing_logs": verify_rebalancing_logs(db_manager),
            "portfolio_snapshots": verify_portfolio_snapshots(db_manager),
            "system_logs": verify_system_logs(db_manager)
        }
        
        print()
        print("📊 테스트 데이터 검증 결과:")
        success_count = 0
        for table, success in results.items():
            status = "✅ 데이터 존재" if success else "❌ 데이터 없음"
            print(f"  {status} {table}")
            if success:
                success_count += 1
        
        print(f"\n🎯 총 {success_count}/{len(results)}개 테이블에 데이터 확인됨")
        
        if success_count == len(results):
            print("\n✅ 모든 테스트 데이터 확인 완료!")
            print("💡 이제 웹 브라우저에서 http://127.0.0.1:5000 접속하여 DB 탭에서 데이터를 확인하세요.")
            return True
        else:
            print("\n⚠️ 일부 테이블에 데이터가 없습니다.")
            print("💡 insert_test_data.py를 다시 실행해보세요.")
            return False
        
    except SystemExit:
        print("❌ 데이터베이스 초기화 실패")
        return False
        
    except Exception as e:
        print(f"❌ 테스트 데이터 검증 실패: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)