# -*- coding: utf-8 -*-
"""
DB 필터 불일치 확인 스크립트
Web API에서 데이터가 안 보이는 원인 분석용

DB에 저장된 실제 portfolio_id, environment 값을 확인합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Scripts"))

import json

def main():
    print("\n" + "=" * 70)
    print("🔍 DB 필터 불일치 확인")
    print("=" * 70)
    
    # DB 설정 로드
    config_path = PROJECT_ROOT / "Config" / "database.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db_cfg = config["database"]
    
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    conn = psycopg2.connect(
        host=db_cfg["host"],
        port=db_cfg["port"],
        dbname=db_cfg["name"],
        user=db_cfg["user"],
        password=db_cfg["password"]
    )
    
    tables = [
        ("trading_history", ["portfolio_id", "environment", "symbol", "order_type", "timestamp"]),
        ("rebalancing_logs", ["portfolio_id", "environment", "rebalance_reason", "status", "timestamp"]),
        ("system_logs", ["level", "module", "environment", "timestamp"]),
        ("portfolio_snapshots", ["portfolio_id", "environment", "total_value", "timestamp"])
    ]
    
    print("\n📌 Web API 기본 필터 값:")
    print("   - portfolio_id = 'default'")
    print("   - environment = 'demo'")
    print()
    
    for table_name, columns in tables:
        print(f"\n{'=' * 50}")
        print(f"📂 테이블: {table_name}")
        print(f"{'=' * 50}")
        
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 총 레코드 수
            cur.execute(f"SELECT COUNT(*) as cnt FROM {table_name}")
            total = cur.fetchone()["cnt"]
            print(f"\n총 레코드 수: {total}")
            
            if total == 0:
                print("   └─ 데이터 없음")
                continue
            
            # portfolio_id, environment 분포 확인
            if "portfolio_id" in columns and "environment" in columns:
                cur.execute(f"""
                    SELECT portfolio_id, environment, COUNT(*) as cnt 
                    FROM {table_name} 
                    GROUP BY portfolio_id, environment
                    ORDER BY cnt DESC
                """)
                distributions = cur.fetchall()
                
                print("\n📊 portfolio_id + environment 조합별 레코드 수:")
                for row in distributions:
                    pid = row["portfolio_id"]
                    env = row["environment"]
                    cnt = row["cnt"]
                    
                    # API 기본값과 일치 여부 표시
                    match = ""
                    if pid == "default" and env == "demo":
                        match = " ✅ (API 기본값과 일치)"
                    else:
                        match = " ⚠️ (API 기본값과 불일치!)"
                    
                    print(f"   - portfolio_id='{pid}', environment='{env}': {cnt}개{match}")
            
            elif "environment" in columns:
                cur.execute(f"""
                    SELECT environment, COUNT(*) as cnt 
                    FROM {table_name} 
                    GROUP BY environment
                    ORDER BY cnt DESC
                """)
                distributions = cur.fetchall()
                
                print("\n📊 environment별 레코드 수:")
                for row in distributions:
                    env = row["environment"]
                    cnt = row["cnt"]
                    match = " ✅" if env == "demo" else " ⚠️"
                    print(f"   - environment='{env}': {cnt}개{match}")
            
            # 최근 레코드 샘플 출력
            cols_str = ", ".join(columns)
            cur.execute(f"""
                SELECT {cols_str} FROM {table_name}
                ORDER BY timestamp DESC
                LIMIT 3
            """)
            samples = cur.fetchall()
            
            print("\n📝 최근 레코드 샘플 (최대 3개):")
            for i, row in enumerate(samples, 1):
                print(f"   [{i}] {dict(row)}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("💡 해결 방법:")
    print("=" * 70)
    print("""
1️⃣  Web API 호출 시 올바른 파라미터 사용:
   curl "http://localhost:5000/api/db/trading-history?portfolio_id=<실제값>&environment=<실제값>"

2️⃣  또는 기존 데이터의 portfolio_id/environment를 'default'/'demo'로 업데이트:
   UPDATE trading_history SET portfolio_id='default', environment='demo';
   UPDATE rebalancing_logs SET portfolio_id='default', environment='demo';

3️⃣  새로운 데이터 저장 시 portfolio_id='default', environment='demo' 사용 확인
""")

if __name__ == "__main__":
    main()
