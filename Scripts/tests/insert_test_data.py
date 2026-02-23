# -*- coding: utf-8 -*-
"""
DB 테스트 데이터 삽입 스크립트
db_test.py에서 데이터를 제대로 읽는지 확인하기 위한 테스트 데이터 생성
"""

import sys
import logging
from pathlib import Path
from datetime import datetime, timedelta
import random

# Scripts 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.db_manager import DatabaseManager
from modules.db_models import TradingHistoryRecord, RebalancingLogRecord, PortfolioSnapshotRecord, SystemLogRecord

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_sample_trading_history(db_manager: DatabaseManager) -> bool:
    """거래 기록 샘플 데이터 생성"""
    print("📈 거래 기록 샘플 데이터 생성...")
    
    # 샘플 종목들
    symbols = [
        {"symbol": "005930", "name": "삼성전자", "price_range": (70000, 80000)},
        {"symbol": "035420", "name": "NAVER", "price_range": (200000, 250000)},
        {"symbol": "000660", "name": "SK하이닉스", "price_range": (80000, 120000)},
        {"symbol": "KRW", "name": "현금", "price_range": (1, 1)},
    ]
    
    success_count = 0
    total_count = 15  # 생성할 총 거래 수
    
    # 최근 7일간의 거래 데이터 생성
    base_date = datetime.now() - timedelta(days=7)
    
    for i in range(total_count):
        try:
            # 랜덤 종목 선택
            stock = random.choice(symbols)
            
            # 거래 시간 (영업일 9-15시 중 랜덤)
            days_offset = random.randint(0, 6)
            hours = random.randint(9, 15)
            minutes = random.randint(0, 59)
            trade_time = base_date + timedelta(days=days_offset, hours=hours, minutes=minutes)
            
            # 거래 데이터 생성
            quantity = random.choice([10, 50, 100, 200]) if stock["symbol"] != "KRW" else random.randint(1000000, 5000000)
            price = random.randint(*stock["price_range"])
            order_type = random.choice(["buy", "sell"]) if stock["symbol"] != "KRW" else "deposit"
            total_amount = quantity * price
            commission = total_amount * 0.002 if stock["symbol"] != "KRW" else 0  # 0.2% 수수료
            
            record = TradingHistoryRecord(
                portfolio_id="demo_portfolio",
                symbol=stock["symbol"],
                order_type=order_type,
                quantity=float(quantity),
                price=float(price),
                total_amount=float(total_amount),
                commission=float(commission),
                order_id=f"ORD{trade_time.strftime('%Y%m%d')}_{i+1:03d}",
                status=random.choice(["completed"] * 8 + ["failed"] * 1 + ["pending"] * 1),  # 대부분 완료
                environment="demo"
            )
            
            if db_manager.save_trading_history(record):
                success_count += 1
                print(f"  ✅ {i+1}/{total_count}: {stock['name']} {order_type} {quantity}주 @ {price:,}원")
            else:
                print(f"  ❌ {i+1}/{total_count}: 저장 실패")
                
        except Exception as e:
            print(f"  ❌ {i+1}/{total_count}: 에러 - {e}")
    
    print(f"  📊 거래 기록 생성 완료: {success_count}/{total_count}건 성공")
    return success_count > 0


def create_sample_rebalancing_logs(db_manager: DatabaseManager) -> bool:
    """리밸런싱 로그 샘플 데이터 생성"""
    print("⚖️ 리밸런싱 로그 샘플 데이터 생성...")
    
    rebalancing_scenarios = [
        {
            "reason": "정기 리밸런싱 - 월간 스케줄",
            "target": {"005930": 0.5, "035420": 0.3, "KRW": 0.2},
            "before": {"005930": 0.45, "035420": 0.35, "KRW": 0.2},
            "after": {"005930": 0.5, "035420": 0.3, "KRW": 0.2},
            "status": "success",
            "orders": 3
        },
        {
            "reason": "임계치 초과 리밸런싱 - 삼성전자 비중 과다",
            "target": {"005930": 0.4, "035420": 0.3, "000660": 0.2, "KRW": 0.1},
            "before": {"005930": 0.55, "035420": 0.25, "000660": 0.15, "KRW": 0.05},
            "after": {"005930": 0.4, "035420": 0.3, "000660": 0.2, "KRW": 0.1},
            "status": "success",
            "orders": 5
        },
        {
            "reason": "시장 급락 대응 리밸런싱",
            "target": {"005930": 0.3, "035420": 0.2, "000660": 0.2, "KRW": 0.3},
            "before": {"005930": 0.4, "035420": 0.3, "000660": 0.25, "KRW": 0.05},
            "after": {"005930": 0.32, "035420": 0.22, "000660": 0.21, "KRW": 0.25},
            "status": "partial",
            "orders": 4,
            "error": "일부 주문 체결 지연"
        }
    ]
    
    success_count = 0
    base_date = datetime.now() - timedelta(days=5)
    
    for i, scenario in enumerate(rebalancing_scenarios):
        try:
            rebalance_time = base_date + timedelta(days=i*2, hours=9)  # 이틀 간격
            
            record = RebalancingLogRecord(
                portfolio_id="demo_portfolio",
                rebalance_reason=scenario["reason"],
                target_weights=scenario["target"],
                before_weights=scenario["before"],
                after_weights=scenario["after"],
                orders_executed=scenario["orders"],
                status=scenario["status"],
                environment="demo",
                error_message=scenario.get("error")
            )
            
            if db_manager.save_rebalancing_log(record):
                success_count += 1
                print(f"  ✅ {i+1}: {scenario['status']} | {scenario['orders']}건 실행 | {scenario['reason'][:30]}...")
            else:
                print(f"  ❌ {i+1}: 저장 실패")
                
        except Exception as e:
            print(f"  ❌ {i+1}: 에러 - {e}")
    
    print(f"  📊 리밸런싱 로그 생성 완료: {success_count}/{len(rebalancing_scenarios)}건 성공")
    return success_count > 0


def create_sample_portfolio_snapshots(db_manager: DatabaseManager) -> bool:
    """포트폴리오 스냅샷 샘플 데이터 생성"""
    print("📸 포트폴리오 스냅샷 샘플 데이터 생성...")
    
    success_count = 0
    base_date = datetime.now() - timedelta(days=10)
    
    # 초기 포트폴리오
    base_total_value = 15000000  # 1500만원
    
    for day in range(10):  # 10일간의 스냅샷
        try:
            snapshot_time = base_date + timedelta(days=day, hours=18)  # 매일 오후 6시
            
            # 일일 변동률 적용 (-5% ~ +5%)
            daily_change = random.uniform(-0.05, 0.05)
            current_total = base_total_value * (1 + daily_change * day * 0.1)
            
            # 포지션 데이터 생성
            positions = {
                "005930": {
                    "symbol": "005930",
                    "name": "삼성전자",
                    "quantity": 100,
                    "current_price": random.randint(72000, 78000),
                    "market_value": 100 * random.randint(72000, 78000),
                    "weight": random.uniform(0.45, 0.55)
                },
                "035420": {
                    "symbol": "035420", 
                    "name": "NAVER",
                    "quantity": 20,
                    "current_price": random.randint(220000, 240000),
                    "market_value": 20 * random.randint(220000, 240000),
                    "weight": random.uniform(0.25, 0.35)
                },
                "000660": {
                    "symbol": "000660",
                    "name": "SK하이닉스", 
                    "quantity": 30,
                    "current_price": random.randint(90000, 110000),
                    "market_value": 30 * random.randint(90000, 110000),
                    "weight": random.uniform(0.15, 0.25)
                },
                "KRW": {
                    "symbol": "KRW",
                    "name": "현금",
                    "quantity": random.randint(2000000, 4000000),
                    "current_price": 1,
                    "market_value": random.randint(2000000, 4000000),
                    "weight": random.uniform(0.1, 0.3)
                }
            }
            
            # 총 자산 재계산
            total_market_value = sum([pos["market_value"] for pos in positions.values()])
            
            record = PortfolioSnapshotRecord(
                portfolio_id="demo_portfolio",
                total_value=float(total_market_value),
                positions=positions,
                environment="demo"
            )
            
            if db_manager.save_portfolio_snapshot(record):
                success_count += 1
                print(f"  ✅ Day {day+1}: 총자산 {total_market_value:,.0f}원 | 포지션 {len(positions)}개")
            else:
                print(f"  ❌ Day {day+1}: 저장 실패")
                
        except Exception as e:
            print(f"  ❌ Day {day+1}: 에러 - {e}")
    
    print(f"  📊 포트폴리오 스냅샷 생성 완료: {success_count}/10건 성공")
    return success_count > 0


def create_sample_system_logs(db_manager: DatabaseManager) -> bool:
    """시스템 로그 샘플 데이터 생성"""
    print("📋 시스템 로그 샘플 데이터 생성...")
    
    log_scenarios = [
        {"level": "INFO", "module": "kis_auth", "message": "KIS API 인증 성공", "extra": {"response_time": 0.3}},
        {"level": "INFO", "module": "portfolio_fetcher", "message": "포트폴리오 데이터 조회 완료", "extra": {"portfolio_count": 5}},
        {"level": "WARNING", "module": "kis_trading", "message": "주문 체결 지연 발생", "extra": {"order_id": "ORD20260222001", "delay_sec": 15}},
        {"level": "INFO", "module": "rebalancing_engine", "message": "리밸런싱 실행 완료", "extra": {"orders_executed": 3, "total_amount": 5000000}},
        {"level": "ERROR", "module": "kis_api_client", "message": "API 호출 실패 - Rate limit 초과", "extra": {"endpoint": "/uapi/overseas-stock/v1/trading/inquire-balance", "retry_after": 60}},
        {"level": "INFO", "module": "db_manager", "message": "데이터베이스 정리 작업 완료", "extra": {"deleted_rows": 150, "tables_cleaned": 4}},
        {"level": "INFO", "module": "scheduler", "message": "일일 스케줄러 작업 시작", "extra": {"scheduled_tasks": 5}},
        {"level": "WARNING", "module": "market_hours", "message": "시장 종료 시간 접근", "extra": {"remaining_minutes": 10}},
        {"level": "INFO", "module": "web_server", "message": "웹 서버 시작", "extra": {"port": 5001, "host": "127.0.0.1"}},
        {"level": "ERROR", "module": "kis_trading", "message": "주문 실행 실패", "extra": {"symbol": "005930", "reason": "잔고 부족"}}
    ]
    
    success_count = 0
    base_date = datetime.now() - timedelta(days=3)
    
    for i, log in enumerate(log_scenarios):
        try:
            # 로그 시간을 최근 3일간 랜덤 분산
            log_time = base_date + timedelta(
                days=random.randint(0, 2),
                hours=random.randint(9, 18),
                minutes=random.randint(0, 59)
            )
            
            record = SystemLogRecord(
                level=log["level"],
                module=log["module"],
                message=log["message"],
                environment="demo",
                extra_data=log["extra"]
            )
            
            if db_manager.save_system_log(record):
                success_count += 1
                print(f"  ✅ {i+1}: {log['level']} | {log['module']} | {log['message'][:40]}...")
            else:
                print(f"  ❌ {i+1}: 저장 실패")
                
        except Exception as e:
            print(f"  ❌ {i+1}: 에러 - {e}")
    
    print(f"  📊 시스템 로그 생성 완료: {success_count}/{len(log_scenarios)}건 성공")
    return success_count > 0


def main():
    """테스트 데이터 삽입 메인 함수"""
    print("🌱 DB 테스트 데이터 삽입 시작")
    print("=" * 60)
    
    try:
        # DatabaseManager 초기화
        print("📡 데이터베이스 연결 중...")
        db_manager = DatabaseManager()
        print("✅ 데이터베이스 연결 성공")
        
        # 각 테이블별 테스트 데이터 생성
        results = {
            "trading_history": create_sample_trading_history(db_manager),
            "rebalancing_logs": create_sample_rebalancing_logs(db_manager),
            "portfolio_snapshots": create_sample_portfolio_snapshots(db_manager),
            "system_logs": create_sample_system_logs(db_manager)
        }
        
        # 결과 요약
        print("\\n📊 테스트 데이터 삽입 결과:")
        success_count = 0
        for table, success in results.items():
            status = "✅ 성공" if success else "❌ 실패"
            print(f"  {status} {table}")
            if success:
                success_count += 1
        
        print(f"\\n🎯 총 {success_count}/{len(results)}개 테이블에 데이터 삽입 완료")
        
        if success_count == len(results):
            print("\\n✅ 모든 테스트 데이터 삽입 완료!")
            print("💡 이제 db_test.py를 실행하여 데이터가 제대로 읽히는지 확인하세요.")
            return True
        else:
            print("\\n⚠️ 일부 테이블에 데이터 삽입 실패")
            return False
        
    except SystemExit:
        print("❌ 데이터베이스 초기화 실패")
        return False
        
    except Exception as e:
        print(f"❌ 테스트 데이터 삽입 실패: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)