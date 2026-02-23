# -*- coding: utf-8 -*-
"""
DB 테스트 데이터 제거 스크립트
insert_test_data.py로 추가된 테스트 데이터를 안전하게 제거
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Scripts 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.db_manager import DatabaseManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def confirm_deletion():
    """삭제 작업 확인"""
    print("⚠️  테스트 데이터 삭제 확인")
    print("=" * 50)
    print("다음 조건의 데이터가 삭제됩니다:")
    print("  - environment = 'demo'인 모든 데이터")
    print("  - portfolio_id가 'demo_portfolio' 또는 'test_'로 시작하는 데이터")
    print("  - symbol이 'TEST'로 시작하는 거래 기록")
    print()
    print("❌ 실제 운영 데이터는 건드리지 않습니다.")
    print()
    
    while True:
        response = input("정말로 테스트 데이터를 삭제하시겠습니까? (yes/no): ").lower().strip()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("'yes' 또는 'no'로 답해주세요.")


def clean_trading_history(db_manager: DatabaseManager) -> dict:
    """거래 기록 테스트 데이터 삭제"""
    print("📈 거래 기록 테스트 데이터 삭제 중...")
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # demo 환경 + 테스트 데이터 삭제
                cur.execute("""
                    DELETE FROM trading_history 
                    WHERE environment = 'demo' 
                    AND (
                        portfolio_id LIKE 'demo_%' 
                        OR portfolio_id LIKE 'test_%'
                        OR symbol LIKE 'TEST%'
                        OR order_id LIKE 'TEST_%'
                        OR order_id LIKE 'ORD%'
                    );
                """)
                
                deleted_count = cur.rowcount
                conn.commit()
                
                print(f"  ✅ 거래 기록 삭제 완료: {deleted_count}건")
                return {"success": True, "deleted": deleted_count, "table": "trading_history"}
                
    except Exception as e:
        print(f"  ❌ 거래 기록 삭제 실패: {e}")
        return {"success": False, "error": str(e), "table": "trading_history"}


def clean_rebalancing_logs(db_manager: DatabaseManager) -> dict:
    """리밸런싱 로그 테스트 데이터 삭제"""
    print("⚖️ 리밸런싱 로그 테스트 데이터 삭제 중...")
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # demo 환경 + 테스트 데이터 삭제
                cur.execute("""
                    DELETE FROM rebalancing_logs 
                    WHERE environment = 'demo' 
                    AND (
                        portfolio_id LIKE 'demo_%' 
                        OR portfolio_id LIKE 'test_%'
                    );
                """)
                
                deleted_count = cur.rowcount
                conn.commit()
                
                print(f"  ✅ 리밸런싱 로그 삭제 완료: {deleted_count}건")
                return {"success": True, "deleted": deleted_count, "table": "rebalancing_logs"}
                
    except Exception as e:
        print(f"  ❌ 리밸런싱 로그 삭제 실패: {e}")
        return {"success": False, "error": str(e), "table": "rebalancing_logs"}


def clean_portfolio_snapshots(db_manager: DatabaseManager) -> dict:
    """포트폴리오 스냅샷 테스트 데이터 삭제"""
    print("📸 포트폴리오 스냅샷 테스트 데이터 삭제 중...")
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # demo 환경 + 테스트 데이터 삭제
                cur.execute("""
                    DELETE FROM portfolio_snapshots 
                    WHERE environment = 'demo' 
                    AND (
                        portfolio_id LIKE 'demo_%' 
                        OR portfolio_id LIKE 'test_%'
                    );
                """)
                
                deleted_count = cur.rowcount
                conn.commit()
                
                print(f"  ✅ 포트폴리오 스냅샷 삭제 완료: {deleted_count}건")
                return {"success": True, "deleted": deleted_count, "table": "portfolio_snapshots"}
                
    except Exception as e:
        print(f"  ❌ 포트폴리오 스냅샷 삭제 실패: {e}")
        return {"success": False, "error": str(e), "table": "portfolio_snapshots"}


def clean_system_logs(db_manager: DatabaseManager) -> dict:
    """시스템 로그 테스트 데이터 삭제"""
    print("📋 시스템 로그 테스트 데이터 삭제 중...")
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                # demo 환경 + 테스트 관련 로그 삭제
                cur.execute("""
                    DELETE FROM system_logs 
                    WHERE environment = 'demo' 
                    AND (
                        module IN ('db_test', 'insert_test_data', 'test_module')
                        OR message LIKE '%테스트%'
                        OR message LIKE '%test%'
                        OR message LIKE '%샘플%'
                        OR message LIKE '%DB 연결 테스트%'
                    );
                """)
                
                deleted_count = cur.rowcount
                conn.commit()
                
                print(f"  ✅ 시스템 로그 삭제 완료: {deleted_count}건")
                return {"success": True, "deleted": deleted_count, "table": "system_logs"}
                
    except Exception as e:
        print(f"  ❌ 시스템 로그 삭제 실패: {e}")
        return {"success": False, "error": str(e), "table": "system_logs"}


def get_current_data_count(db_manager: DatabaseManager) -> dict:
    """현재 데이터 개수 조회 (삭제 전 확인용)"""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                counts = {}
                
                # 각 테이블별 demo 환경 데이터 개수 조회
                tables = [
                    ("trading_history", "portfolio_id LIKE 'demo_%' OR portfolio_id LIKE 'test_%' OR symbol LIKE 'TEST%'"),
                    ("rebalancing_logs", "portfolio_id LIKE 'demo_%' OR portfolio_id LIKE 'test_%'"),
                    ("portfolio_snapshots", "portfolio_id LIKE 'demo_%' OR portfolio_id LIKE 'test_%'"),
                    ("system_logs", "module IN ('db_test', 'insert_test_data', 'test_module') OR message LIKE '%테스트%' OR message LIKE '%test%'")
                ]
                
                for table_name, condition in tables:
                    cur.execute(f"""
                        SELECT COUNT(*) FROM {table_name} 
                        WHERE environment = 'demo' AND ({condition});
                    """)
                    count = cur.fetchone()[0]
                    counts[table_name] = count
                
                return counts
                
    except Exception as e:
        logger.error(f"데이터 개수 조회 실패: {e}")
        return {}


def main():
    """테스트 데이터 삭제 메인 함수"""
    print("🧹 DB 테스트 데이터 삭제 도구")
    print("=" * 60)
    
    try:
        # 사용자 확인
        if not confirm_deletion():
            print("❌ 삭제 작업이 취소되었습니다.")
            return False
        
        print("\\n📡 데이터베이스 연결 중...")
        db_manager = DatabaseManager()
        print("✅ 데이터베이스 연결 성공")
        
        # 삭제 전 데이터 개수 확인
        print("\\n📊 삭제 대상 데이터 개수 확인:")
        before_counts = get_current_data_count(db_manager)
        
        total_before = 0
        for table, count in before_counts.items():
            print(f"  {table}: {count}건")
            total_before += count
        
        if total_before == 0:
            print("\\n💡 삭제할 테스트 데이터가 없습니다.")
            return True
        
        print(f"\\n🎯 총 {total_before}건의 테스트 데이터를 삭제합니다.")
        
        # 최종 확인
        final_confirm = input("\\n계속 진행하시겠습니까? (yes/no): ").lower().strip()
        if final_confirm not in ['yes', 'y']:
            print("❌ 삭제 작업이 취소되었습니다.")
            return False
        
        print("\\n🗑️ 테스트 데이터 삭제 시작...")
        
        # 각 테이블별 삭제 실행
        cleanup_functions = [
            clean_trading_history,
            clean_rebalancing_logs,
            clean_portfolio_snapshots,
            clean_system_logs
        ]
        
        results = []
        for cleanup_func in cleanup_functions:
            result = cleanup_func(db_manager)
            results.append(result)
        
        # 결과 요약
        print("\\n📊 테스트 데이터 삭제 결과:")
        success_count = 0
        total_deleted = 0
        
        for result in results:
            if result["success"]:
                deleted = result["deleted"]
                table = result["table"]
                status = "✅ 성공"
                print(f"  {status} {table}: {deleted}건 삭제")
                success_count += 1
                total_deleted += deleted
            else:
                table = result["table"]
                error = result["error"]
                status = "❌ 실패"
                print(f"  {status} {table}: {error}")
        
        print(f"\\n🎯 최종 결과: {success_count}/{len(results)}개 테이블 처리 완료")
        print(f"📈 총 {total_deleted}건의 테스트 데이터 삭제")
        
        if success_count == len(results):
            print("\\n✅ 모든 테스트 데이터 삭제 완료!")
            print("💡 이제 깨끗한 상태에서 새로운 테스트를 시작할 수 있습니다.")
        else:
            print("\\n⚠️ 일부 테이블에서 삭제 실패")
        
        # 삭제 후 데이터 개수 재확인
        print("\\n🔍 삭제 후 데이터 개수 확인:")
        after_counts = get_current_data_count(db_manager)
        
        total_after = 0
        for table, count in after_counts.items():
            print(f"  {table}: {count}건")
            total_after += count
        
        if total_after == 0:
            print("\\n🎉 모든 테스트 데이터가 성공적으로 삭제되었습니다!")
        else:
            print(f"\\n⚠️ {total_after}건의 데이터가 남아있습니다. 조건에 맞지 않는 데이터일 수 있습니다.")
        
        return success_count == len(results)
        
    except SystemExit:
        print("❌ 데이터베이스 초기화 실패")
        return False
        
    except Exception as e:
        print(f"❌ 테스트 데이터 삭제 실패: {e}")
        return False


def selective_cleanup():
    """선택적 데이터 삭제 (개발 중 임시 사용)"""
    print("🔧 선택적 테스트 데이터 삭제")
    print("=" * 40)
    
    tables = {
        "1": ("trading_history", "거래 기록"),
        "2": ("rebalancing_logs", "리밸런싱 로그"),  
        "3": ("portfolio_snapshots", "포트폴리오 스냅샷"),
        "4": ("system_logs", "시스템 로그"),
        "5": ("all", "모든 테이블")
    }
    
    print("삭제할 테이블을 선택하세요:")
    for key, (table, desc) in tables.items():
        print(f"  {key}. {desc}")
    
    choice = input("\\n선택 (1-5): ").strip()
    
    if choice not in tables:
        print("❌ 잘못된 선택입니다.")
        return False
    
    if choice == "5":
        return main()  # 전체 삭제
    else:
        # 개별 테이블 삭제 로직 (구현 생략)
        print(f"💡 {tables[choice][1]} 삭제는 main() 함수를 사용하세요.")
        return False


if __name__ == "__main__":
    mode = input("실행 모드를 선택하세요 (1: 전체 삭제, 2: 선택적 삭제): ").strip()
    
    if mode == "1":
        success = main()
    elif mode == "2":
        success = selective_cleanup()
    else:
        print("❌ 잘못된 모드 선택")
        success = False
    
    sys.exit(0 if success else 1)