# -*- coding: utf-8 -*-
"""
DB 및 Web 서버 진단 스크립트
운영 서버에서 DB 데이터가 웹에 표시되지 않을 때 문제 원인을 파악하기 위한 도구

사용법:
    python Scripts/tests/db_web_diagnostic.py --all
    python Scripts/tests/db_web_diagnostic.py --db-only
    python Scripts/tests/db_web_diagnostic.py --web-only
    python Scripts/tests/db_web_diagnostic.py --check-data
"""

import os
import sys
import json
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# 프로젝트 루트 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "Scripts"))

# 환경 변수로 DB 설정 덮어쓰기 가능
DB_HOST = os.getenv("DB_HOST", None)
DB_PORT = os.getenv("DB_PORT", None)
DB_NAME = os.getenv("DB_NAME", None)
DB_USER = os.getenv("DB_USER", None)
DB_PASSWORD = os.getenv("DB_PASSWORD", None)

# 웹 서버 설정
WEB_HOST = os.getenv("WEB_HOST", "localhost")
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))


class DiagnosticResult:
    """진단 결과를 저장하는 클래스"""
    
    def __init__(self):
        self.results = {}
        self.errors = []
        self.warnings = []
        self.timestamp = datetime.now().isoformat()
    
    def add_result(self, category: str, test_name: str, success: bool, 
                   message: str, data: Any = None):
        if category not in self.results:
            self.results[category] = []
        
        self.results[category].append({
            "test": test_name,
            "success": success,
            "message": message,
            "data": data
        })
        
        if not success:
            self.errors.append(f"[{category}] {test_name}: {message}")
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def print_summary(self):
        """진단 결과 요약 출력"""
        print("\n" + "=" * 70)
        print("📋 DB/Web 진단 결과 요약")
        print("=" * 70)
        print(f"시각: {self.timestamp}")
        print()
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.results.items():
            print(f"\n📂 {category}")
            print("-" * 50)
            
            for test in tests:
                total_tests += 1
                status = "✅" if test["success"] else "❌"
                if test["success"]:
                    passed_tests += 1
                
                print(f"  {status} {test['test']}")
                print(f"      └─ {test['message']}")
                
                if test["data"] and not test["success"]:
                    print(f"      └─ Data: {test['data']}")
        
        print("\n" + "=" * 70)
        print(f"📊 결과: {passed_tests}/{total_tests} 테스트 통과")
        
        if self.warnings:
            print(f"\n⚠️  경고 ({len(self.warnings)}개):")
            for warning in self.warnings:
                print(f"    - {warning}")
        
        if self.errors:
            print(f"\n❌ 오류 ({len(self.errors)}개):")
            for error in self.errors:
                print(f"    - {error}")
            print("\n💡 문제 해결 방법:")
            self._print_solution_hints()
        else:
            print("\n✅ 모든 테스트 통과! DB와 Web 연결이 정상입니다.")
        
        print("=" * 70)
    
    def _print_solution_hints(self):
        """에러에 따른 해결 방법 출력"""
        hints = []
        
        for error in self.errors:
            if "connection" in error.lower() or "연결" in error:
                hints.append("1. DB 서버가 실행 중인지 확인: PostgreSQL 서비스 상태 확인")
                hints.append("2. DB 설정 확인: Config/database.json의 host, port, user, password 검증")
                hints.append("3. 방화벽/네트워크 확인: 해당 포트(5432)가 열려있는지 확인")
            
            if "table" in error.lower() or "테이블" in error:
                hints.append("4. 테이블 생성 필요: db_manager.create_tables() 실행")
            
            if "empty" in error.lower() or "데이터 없음" in error:
                hints.append("5. 데이터 삽입 확인: 리밸런싱 또는 거래 기록이 생성되었는지 확인")
            
            if "web" in error.lower() or "api" in error.lower():
                hints.append("6. 웹 서버 확인: 웹 서버가 실행 중인지 확인")
                hints.append("7. 포트 확인: 웹 서버 포트(5000)가 사용 가능한지 확인")
        
        # 중복 제거
        for hint in sorted(set(hints)):
            print(f"    {hint}")


class DBDiagnostic:
    """데이터베이스 진단 클래스"""
    
    def __init__(self, result: DiagnosticResult):
        self.result = result
        self.conn = None
        self.config = None
    
    def load_config(self) -> Tuple[bool, str]:
        """DB 설정 파일 로드"""
        config_path = PROJECT_ROOT / "Config" / "database.json"
        
        if not config_path.exists():
            return False, f"설정 파일이 존재하지 않습니다: {config_path}"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # 환경 변수로 덮어쓰기
            if DB_HOST:
                self.config["database"]["host"] = DB_HOST
            if DB_PORT:
                self.config["database"]["port"] = int(DB_PORT)
            if DB_NAME:
                self.config["database"]["name"] = DB_NAME
            if DB_USER:
                self.config["database"]["user"] = DB_USER
            if DB_PASSWORD:
                self.config["database"]["password"] = DB_PASSWORD
            
            return True, "설정 파일 로드 성공"
        except Exception as e:
            return False, f"설정 파일 로드 실패: {e}"
    
    def test_psycopg2_import(self) -> Tuple[bool, str]:
        """psycopg2 패키지 임포트 테스트"""
        try:
            import psycopg2
            version = psycopg2.__version__
            return True, f"psycopg2 버전: {version}"
        except ImportError:
            return False, "psycopg2가 설치되지 않았습니다. pip install psycopg2-binary"
    
    def test_connection(self) -> Tuple[bool, str]:
        """DB 연결 테스트"""
        try:
            import psycopg2
            
            db_cfg = self.config["database"]
            self.conn = psycopg2.connect(
                host=db_cfg["host"],
                port=db_cfg["port"],
                dbname=db_cfg["name"],
                user=db_cfg["user"],
                password=db_cfg["password"],
                sslmode=db_cfg.get("sslmode", "prefer"),
                connect_timeout=db_cfg.get("connect_timeout", 5)
            )
            
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                if result and result[0] == 1:
                    return True, f"연결 성공! (host={db_cfg['host']}, db={db_cfg['name']})"
            
            return False, "연결은 됐으나 SELECT 1 실패"
        
        except Exception as e:
            return False, f"연결 실패: {e}"
    
    def test_tables_exist(self) -> Tuple[bool, str, Dict]:
        """테이블 존재 여부 확인"""
        required_tables = [
            "trading_history",
            "rebalancing_logs", 
            "portfolio_snapshots",
            "system_logs"
        ]
        
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                existing_tables = [row[0] for row in cur.fetchall()]
            
            missing_tables = [t for t in required_tables if t not in existing_tables]
            found_tables = [t for t in required_tables if t in existing_tables]
            
            if missing_tables:
                return False, f"누락된 테이블: {missing_tables}", {
                    "found": found_tables,
                    "missing": missing_tables
                }
            
            return True, f"모든 필수 테이블 존재: {found_tables}", {
                "found": found_tables,
                "missing": []
            }
        
        except Exception as e:
            return False, f"테이블 확인 실패: {e}", {}
    
    def test_table_data(self, table_name: str) -> Tuple[bool, str, Dict]:
        """특정 테이블의 데이터 존재 여부 확인"""
        try:
            with self.conn.cursor() as cur:
                # 레코드 수 확인
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                
                # 최근 레코드 확인
                cur.execute(f"""
                    SELECT * FROM {table_name} 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """)
                recent_records = cur.fetchall()
                
                # 컬럼명 가져오기
                columns = [desc[0] for desc in cur.description]
            
            if count == 0:
                return False, f"테이블 '{table_name}'에 데이터 없음 (0 rows)", {
                    "count": 0,
                    "recent_records": []
                }
            
            return True, f"테이블 '{table_name}'에 {count}개 레코드 존재", {
                "count": count,
                "columns": columns,
                "recent_records": len(recent_records)
            }
        
        except Exception as e:
            return False, f"테이블 '{table_name}' 데이터 확인 실패: {e}", {}
    
    def test_db_manager_module(self) -> Tuple[bool, str]:
        """db_manager 모듈 임포트 테스트"""
        try:
            from modules.db_manager import DatabaseManager
            return True, "db_manager 모듈 임포트 성공"
        except Exception as e:
            return False, f"db_manager 모듈 임포트 실패: {e}"
    
    def test_db_manager_connection(self) -> Tuple[bool, str]:
        """DatabaseManager를 통한 연결 테스트"""
        try:
            from modules.db_manager import DatabaseManager
            
            db_manager = DatabaseManager()
            if db_manager.test_connection():
                return True, "DatabaseManager 연결 테스트 성공"
            return False, "DatabaseManager 연결 테스트 실패"
        
        except Exception as e:
            return False, f"DatabaseManager 테스트 실패: {e}"
    
    def run_all_tests(self):
        """모든 DB 테스트 실행"""
        category = "Database"
        
        # 1. psycopg2 임포트 테스트
        success, message = self.test_psycopg2_import()
        self.result.add_result(category, "psycopg2 패키지", success, message)
        if not success:
            return  # psycopg2 없으면 다른 테스트 불가
        
        # 2. 설정 파일 로드
        success, message = self.load_config()
        self.result.add_result(category, "설정 파일 로드", success, message)
        if not success:
            return
        
        # 3. DB 연결 테스트
        success, message = self.test_connection()
        self.result.add_result(category, "DB 연결", success, message)
        if not success:
            return
        
        # 4. 테이블 존재 확인
        success, message, data = self.test_tables_exist()
        self.result.add_result(category, "테이블 존재", success, message, data)
        
        # 5. 각 테이블 데이터 확인
        tables = ["trading_history", "rebalancing_logs", 
                  "portfolio_snapshots", "system_logs"]
        
        for table in tables:
            try:
                success, message, data = self.test_table_data(table)
                self.result.add_result(category, f"'{table}' 데이터", success, message, data)
            except Exception as e:
                self.result.add_result(category, f"'{table}' 데이터", False, str(e))
        
        # 6. db_manager 모듈 테스트
        success, message = self.test_db_manager_module()
        self.result.add_result(category, "db_manager 모듈", success, message)
        
        # 7. DatabaseManager 연결 테스트
        success, message = self.test_db_manager_connection()
        self.result.add_result(category, "DatabaseManager 연결", success, message)
        
        # 연결 닫기
        if self.conn:
            self.conn.close()


class WebDiagnostic:
    """웹 서버 진단 클래스"""
    
    def __init__(self, result: DiagnosticResult, host: str = "localhost", port: int = 5000):
        self.result = result
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
    
    def test_requests_import(self) -> Tuple[bool, str]:
        """requests 패키지 임포트 테스트"""
        try:
            import requests
            return True, f"requests 버전: {requests.__version__}"
        except ImportError:
            return False, "requests가 설치되지 않았습니다. pip install requests"
    
    def test_server_running(self) -> Tuple[bool, str]:
        """웹 서버 실행 여부 확인"""
        import socket
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                return True, f"웹 서버 포트 {self.port} 열려있음"
            return False, f"웹 서버 포트 {self.port}에 연결 불가 (서버 미실행?)"
        
        except Exception as e:
            return False, f"포트 확인 실패: {e}"
    
    def test_health_endpoint(self) -> Tuple[bool, str, Dict]:
        """헬스 체크 엔드포인트 테스트"""
        try:
            import requests
            
            url = f"{self.base_url}/health"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                db_status = data.get("db_status", "unknown")
                api_status = data.get("api_status", "unknown")
                
                # DB 또는 API가 disconnected면 경고
                if db_status != "connected":
                    self.result.add_warning(f"헬스 체크에서 DB 상태: {db_status}")
                if api_status != "connected":
                    self.result.add_warning(f"헬스 체크에서 API 상태: {api_status}")
                
                return True, f"헬스 체크 성공 (db={db_status}, api={api_status})", data
            
            return False, f"헬스 체크 실패: HTTP {response.status_code}", {}
        
        except Exception as e:
            return False, f"헬스 체크 요청 실패: {e}", {}
    
    def test_trading_history_api(self) -> Tuple[bool, str, Dict]:
        """거래 기록 API 테스트"""
        try:
            import requests
            
            url = f"{self.base_url}/api/db/trading-history"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                count = data.get("total", 0)
                records = data.get("data", [])
                
                if count == 0:
                    return True, f"API 정상이나 데이터 없음 (0 rows)", data
                
                return True, f"거래 기록 {count}개 조회 성공", data
            
            return False, f"API 오류: HTTP {response.status_code} - {response.text}", {}
        
        except Exception as e:
            return False, f"API 요청 실패: {e}", {}
    
    def test_portfolio_snapshots_api(self) -> Tuple[bool, str, Dict]:
        """포트폴리오 스냅샷 API 테스트"""
        try:
            import requests
            
            url = f"{self.base_url}/api/db/portfolio-snapshots"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                count = data.get("total", 0)
                
                if count == 0:
                    return True, f"API 정상이나 데이터 없음", data
                
                return True, f"스냅샷 {count}개 조회 성공", data
            
            return False, f"API 오류: HTTP {response.status_code}", {}
        
        except Exception as e:
            return False, f"API 요청 실패: {e}", {}
    
    def test_rebalancing_logs_api(self) -> Tuple[bool, str, Dict]:
        """리밸런싱 로그 API 테스트"""
        try:
            import requests
            
            url = f"{self.base_url}/api/db/rebalancing-logs"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                count = data.get("total", 0)
                
                if count == 0:
                    return True, f"API 정상이나 데이터 없음", data
                
                return True, f"리밸런싱 로그 {count}개 조회 성공", data
            
            return False, f"API 오류: HTTP {response.status_code}", {}
        
        except Exception as e:
            return False, f"API 요청 실패: {e}", {}
    
    def test_main_page(self) -> Tuple[bool, str]:
        """메인 페이지 접속 테스트"""
        try:
            import requests
            
            url = f"{self.base_url}/"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                # HTML 응답 확인
                content_type = response.headers.get("Content-Type", "")
                if "html" in content_type:
                    return True, "메인 페이지 로드 성공 (HTML)"
                return True, f"메인 페이지 로드 성공 ({content_type})"
            
            return False, f"메인 페이지 로드 실패: HTTP {response.status_code}"
        
        except Exception as e:
            return False, f"메인 페이지 요청 실패: {e}"
    
    def run_all_tests(self):
        """모든 웹 테스트 실행"""
        category = "Web Server"
        
        # 1. requests 임포트 테스트
        success, message = self.test_requests_import()
        self.result.add_result(category, "requests 패키지", success, message)
        if not success:
            return
        
        # 2. 웹 서버 실행 여부
        success, message = self.test_server_running()
        self.result.add_result(category, "서버 포트 연결", success, message)
        if not success:
            self.result.add_warning(f"웹 서버가 실행 중이지 않습니다. portfolio_web_app.py를 실행해주세요.")
            return
        
        # 3. 메인 페이지
        success, message = self.test_main_page()
        self.result.add_result(category, "메인 페이지", success, message)
        
        # 4. 헬스 체크
        success, message, data = self.test_health_endpoint()
        self.result.add_result(category, "헬스 체크 API", success, message, data)
        
        # 5. 거래 기록 API
        success, message, data = self.test_trading_history_api()
        self.result.add_result(category, "거래 기록 API", success, message, data)
        
        # 6. 포트폴리오 스냅샷 API
        success, message, data = self.test_portfolio_snapshots_api()
        self.result.add_result(category, "포트폴리오 스냅샷 API", success, message, data)
        
        # 7. 리밸런싱 로그 API
        success, message, data = self.test_rebalancing_logs_api()
        self.result.add_result(category, "리밸런싱 로그 API", success, message, data)


def show_quick_queries():
    """DB 직접 확인용 SQL 쿼리 출력"""
    print("\n" + "=" * 70)
    print("🔍 DB 직접 확인용 SQL 쿼리")
    print("=" * 70)
    
    queries = {
        "테이블 목록 확인": """
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';""",
        
        "거래 기록 최근 10개": """
SELECT id, portfolio_id, symbol, order_type, quantity, price, 
       timestamp, status, environment 
FROM trading_history 
ORDER BY timestamp DESC LIMIT 10;""",
        
        "리밸런싱 로그 최근 10개": """
SELECT id, portfolio_id, rebalance_reason, orders_executed, 
       status, timestamp, environment 
FROM rebalancing_logs 
ORDER BY timestamp DESC LIMIT 10;""",
        
        "포트폴리오 스냅샷 최근 5개": """
SELECT id, portfolio_id, total_value, timestamp, environment 
FROM portfolio_snapshots 
ORDER BY timestamp DESC LIMIT 5;""",
        
        "각 테이블 레코드 수": """
SELECT 'trading_history' as table_name, COUNT(*) as count FROM trading_history
UNION ALL
SELECT 'rebalancing_logs', COUNT(*) FROM rebalancing_logs
UNION ALL  
SELECT 'portfolio_snapshots', COUNT(*) FROM portfolio_snapshots
UNION ALL
SELECT 'system_logs', COUNT(*) FROM system_logs;"""
    }
    
    for name, query in queries.items():
        print(f"\n📌 {name}:")
        print(f"```sql{query}\n```")
    
    print("\n" + "=" * 70)
    print("💡 PostgreSQL 접속 명령어:")
    print("   psql -h <host> -p 5432 -U appuser -d appdb")
    print("=" * 70)


def show_web_endpoints():
    """웹 API 엔드포인트 확인 방법 출력"""
    print("\n" + "=" * 70)
    print("🌐 Web API 엔드포인트 확인 방법")
    print("=" * 70)
    
    endpoints = {
        "헬스 체크": "/health",
        "메인 페이지": "/",
        "포트폴리오 API": "/api/portfolio",
        "거래 기록 API": "/api/db/trading-history?portfolio_id=default&environment=demo",
        "리밸런싱 로그 API": "/api/db/rebalancing-logs?portfolio_id=default&environment=demo",
        "포트폴리오 스냅샷 API": "/api/db/portfolio-snapshots?portfolio_id=default&environment=demo",
        "시스템 로그 API": "/api/db/system-logs?level=INFO&environment=demo"
    }
    
    base_url = f"http://{WEB_HOST}:{WEB_PORT}"
    
    print(f"\n기본 URL: {base_url}")
    print()
    
    for name, endpoint in endpoints.items():
        print(f"📌 {name}:")
        print(f"   curl {base_url}{endpoint}")
        print()
    
    print("\n💡 cURL로 JSON 응답 확인:")
    print(f"   curl -s {base_url}/health | python -m json.tool")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="DB 및 Web 서버 진단 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
    python db_web_diagnostic.py --all               # 모든 테스트 실행
    python db_web_diagnostic.py --db-only           # DB 테스트만 실행
    python db_web_diagnostic.py --web-only          # Web 테스트만 실행
    python db_web_diagnostic.py --show-queries      # DB 확인용 SQL 쿼리 출력
    python db_web_diagnostic.py --show-endpoints    # Web API 엔드포인트 출력
    
환경 변수로 설정 덮어쓰기:
    DB_HOST=<host> DB_PORT=<port> python db_web_diagnostic.py --db-only
    WEB_HOST=<host> WEB_PORT=<port> python db_web_diagnostic.py --web-only
        """
    )
    
    parser.add_argument("--all", action="store_true", help="모든 테스트 실행")
    parser.add_argument("--db-only", action="store_true", help="DB 테스트만 실행")
    parser.add_argument("--web-only", action="store_true", help="Web 테스트만 실행")
    parser.add_argument("--show-queries", action="store_true", help="DB 확인용 SQL 쿼리 출력")
    parser.add_argument("--show-endpoints", action="store_true", help="Web API 엔드포인트 출력")
    parser.add_argument("--web-host", default=WEB_HOST, help="웹 서버 호스트")
    parser.add_argument("--web-port", type=int, default=WEB_PORT, help="웹 서버 포트")
    
    args = parser.parse_args()
    
    # 아무 옵션도 없으면 --all로 처리
    if not any([args.all, args.db_only, args.web_only, args.show_queries, args.show_endpoints]):
        args.all = True
    
    if args.show_queries:
        show_quick_queries()
        return
    
    if args.show_endpoints:
        show_web_endpoints()
        return
    
    # 진단 실행
    result = DiagnosticResult()
    
    print("\n🔧 Investment_Auto DB/Web 진단 시작...")
    print(f"   시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.all or args.db_only:
        print("\n📊 DB 테스트 실행 중...")
        db_diag = DBDiagnostic(result)
        db_diag.run_all_tests()
    
    if args.all or args.web_only:
        print("\n🌐 Web 테스트 실행 중...")
        web_diag = WebDiagnostic(result, args.web_host, args.web_port)
        web_diag.run_all_tests()
    
    # 결과 출력
    result.print_summary()


if __name__ == "__main__":
    main()
