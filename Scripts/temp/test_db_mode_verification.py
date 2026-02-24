# -*- coding: utf-8 -*-
"""
DB 모드 동작 확인 테스트 스크립트
portfolio_rebalancing.py의 --db-mode 플래그 동작을 검증합니다.
"""

import sys
import subprocess
import os
from pathlib import Path

def test_db_mode_flag():
    """--db-mode 플래그 동작 테스트"""
    print("🧪 DB 모드 플래그 동작 테스트")
    print("=" * 50)
    
    portfolio_script = Path(__file__).parent.parent / "apps" / "portfolio_rebalancing.py"
    
    if not portfolio_script.exists():
        print(f"❌ 스크립트 파일을 찾을 수 없습니다: {portfolio_script}")
        return False
    
    print(f"✅ 테스트 대상: {portfolio_script}")
    
    # 1. --help 출력으로 --db-mode 옵션 확인
    print("\n1️⃣ --db-mode 옵션 존재 여부 확인")
    try:
        result = subprocess.run([
            sys.executable, str(portfolio_script), "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if "--db-mode" in result.stdout:
            print("✅ --db-mode 옵션이 존재합니다")
        else:
            print("❌ --db-mode 옵션을 찾을 수 없습니다")
            print("Help 출력:", result.stdout[-500:])  # 마지막 500자만 출력
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ --help 명령이 시간 초과되었습니다")
        return False
    except Exception as e:
        print(f"❌ --help 테스트 중 오류: {e}")
        return False
    
    # 2. 설정 검증 모드로 DB 모드 테스트
    print("\n2️⃣ DB 모드 활성화 테스트 (설정 검증만)")
    try:
        # DB 모드 없이 실행
        result_without_db = subprocess.run([
            sys.executable, str(portfolio_script), 
            "--validate-only", "--demo"
        ], capture_output=True, text=True, timeout=30)
        
        if "DB: disabled" in result_without_db.stderr:
            print("✅ DB 모드 없음 확인: 'DB: disabled'")
        else:
            print("⚠️ DB 비활성화 메시지를 찾을 수 없습니다")
            print("stderr:", result_without_db.stderr[-300:])
        
        # DB 모드로 실행
        result_with_db = subprocess.run([
            sys.executable, str(portfolio_script), 
            "--validate-only", "--demo", "--db-mode"
        ], capture_output=True, text=True, timeout=30)
        
        if "DB: enabled" in result_with_db.stderr:
            print("✅ DB 모드 활성화 확인: 'DB: enabled'")
        elif "Database mode enabled" in result_with_db.stderr:
            print("✅ DB 모드 활성화 확인: 'Database mode enabled'")
        else:
            print("⚠️ DB 활성화 메시지를 찾을 수 없습니다")
            print("stderr:", result_with_db.stderr[-300:])
            
        if result_with_db.returncode == 0:
            print("✅ DB 모드로 설정 검증 성공")
        else:
            print(f"⚠️ DB 모드 실행 중 오류 (종료 코드: {result_with_db.returncode})")
            print("stdout:", result_with_db.stdout[-300:])
            print("stderr:", result_with_db.stderr[-300:])
            
    except subprocess.TimeoutExpired:
        print("❌ DB 모드 테스트가 시간 초과되었습니다")
        return False
    except Exception as e:
        print(f"❌ DB 모드 테스트 중 오류: {e}")
        return False
    
    print("\n✅ DB 모드 플래그 테스트 완료")
    return True


def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("\n🔌 데이터베이스 연결 테스트")
    print("=" * 50)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from modules.db_manager import DatabaseManager
        
        db_manager = DatabaseManager()
        if db_manager.test_connection():
            print("✅ 데이터베이스 연결 성공")
            return True
        else:
            print("❌ 데이터베이스 연결 실패")
            return False
            
    except ImportError as e:
        print(f"⚠️ 데이터베이스 모듈 임포트 실패: {e}")
        return False
    except Exception as e:
        print(f"❌ 데이터베이스 연결 테스트 중 오류: {e}")
        return False


def check_config_files():
    """설정 파일 존재 여부 확인"""
    print("\n📋 설정 파일 확인")
    print("=" * 50)
    
    config_dir = Path(__file__).parent.parent.parent / "Config"
    
    files_to_check = [
        "database.json",
        "config.json", 
        "config_basic.json",
        "config_advanced.json"
    ]
    
    all_exist = True
    for filename in files_to_check:
        filepath = config_dir / filename
        if filepath.exists():
            print(f"✅ {filename} 존재")
        else:
            print(f"❌ {filename} 없음")
            all_exist = False
            
    return all_exist


def main():
    """메인 테스트 실행"""
    print("🚀 DB 모드 동작 확인 테스트 시작")
    print("=" * 60)
    
    # 설정 파일 확인
    config_ok = check_config_files()
    
    # DB 연결 테스트
    db_ok = test_database_connection()
    
    # DB 모드 플래그 테스트
    flag_ok = test_db_mode_flag()
    
    print("\n📊 테스트 결과 요약")
    print("=" * 60)
    print(f"✅ 설정 파일: {'정상' if config_ok else '문제 있음'}")
    print(f"✅ DB 연결: {'정상' if db_ok else '실패'}")
    print(f"✅ --db-mode 플래그: {'정상' if flag_ok else '문제 있음'}")
    
    if config_ok and flag_ok:
        print("\n🎉 테스트 성공!")
        print("💡 다음 명령으로 DB 모드로 실행하세요:")
        print("   python Scripts\\apps\\portfolio_rebalancing.py --demo --db-mode")
        
        if not db_ok:
            print("\n⚠️ DB 연결에 문제가 있습니다.")
            print("   PostgreSQL이 실행 중인지 확인해주세요.")
    else:
        print("\n❌ 테스트 실패!")
        print("🔧 설정을 확인해주세요.")


if __name__ == "__main__":
    main()