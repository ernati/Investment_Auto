# -*- coding: utf-8 -*-
"""
웹 브라우저 DB 데이터 확인 스크립트
웹 인터페이스에서 DB 데이터가 제대로 출력되는지 확인
"""

import sys
import logging
import time
from pathlib import Path
import requests

# Scripts 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_web_api(base_url="http://127.0.0.1:5001"):
    """웹 API 테스트"""
    print("🌐 웹 API 테스트 시작")
    print("=" * 60)
    
    # 테스트할 API 엔드포인트들
    test_apis = [
        {
            "name": "거래 기록",
            "url": f"{base_url}/api/db/trading-history?portfolio_id=demo_portfolio&limit=5",
            "icon": "💰"
        },
        {
            "name": "리밸런싱 로그", 
            "url": f"{base_url}/api/db/rebalancing-logs?portfolio_id=demo_portfolio&limit=5",
            "icon": "⚖️"
        },
        {
            "name": "포트폴리오 스냅샷",
            "url": f"{base_url}/api/db/portfolio-snapshots?portfolio_id=demo_portfolio&limit=5", 
            "icon": "📊"
        },
        {
            "name": "시스템 로그",
            "url": f"{base_url}/api/db/system-logs?limit=5",
            "icon": "📋"
        }
    ]
    
    results = {}
    
    # 각 API 테스트
    for api in test_apis:
        print(f"{api['icon']} {api['name']} 테스트...")
        
        try:
            response = requests.get(api['url'], timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'error' in data:
                    print(f"  ❌ API 에러: {data['error']}")
                    results[api['name']] = False
                else:
                    record_count = len(data.get('data', []))
                    print(f"  ✅ 성공: {record_count}건 조회됨")
                    
                    # 첫 번째 레코드가 있으면 간단한 정보 출력
                    if record_count > 0:
                        first_record = data['data'][0]
                        print(f"  📄 첫 번째 레코드: {list(first_record.keys())[:5]}...")
                    
                    results[api['name']] = True
                
            else:
                print(f"  ❌ HTTP 에러: {response.status_code}")
                results[api['name']] = False
                
        except requests.exceptions.ConnectionError:
            print(f"  ❌ 연결 실패: 웹 서버가 실행 중인지 확인하세요 ({base_url})")
            results[api['name']] = False
        except requests.exceptions.Timeout:
            print(f"  ❌ 타임아웃: API 응답 시간 초과")
            results[api['name']] = False
        except Exception as e:
            print(f"  ❌ 에러: {e}")
            results[api['name']] = False
        
        time.sleep(0.5)  # API 호출 간 잠깐 대기
    
    # 결과 요약
    print("\n📊 API 테스트 결과:")
    success_count = 0
    for name, success in results.items():
        status = "✅ 정상" if success else "❌ 실패"
        print(f"  {status} {name}")
        if success:
            success_count += 1
    
    print(f"\n🎯 총 {success_count}/{len(results)}개 API 정상 작동")
    
    if success_count == len(results):
        print("\n✅ 모든 API가 정상 작동합니다!")
        print(f"💻 웹 브라우저에서 확인: {base_url}")
        print("🗄️ '데이터베이스' 탭을 클릭하여 DB 데이터를 확인하세요.")
        return True
    else:
        print("\n⚠️ 일부 API에 문제가 있습니다.")
        print("🔧 웹 서버 상태와 데이터베이스 연결을 확인해주세요.")
        return False


def check_web_server_status(base_url="http://127.0.0.1:5001"):
    """웹 서버 상태 확인"""
    print("🔍 웹 서버 상태 확인...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"  ✅ 서버 상태: {health_data.get('status', 'Unknown')}")
            print(f"  🌐 환경: {health_data.get('environment', 'Unknown')}")
            print(f"  📡 API 상태: {health_data.get('api_status', 'Unknown')}")
            print(f"  🗄️ DB 상태: {health_data.get('db_status', 'Unknown')}")
            return True
        else:
            print(f"  ❌ 서버 응답 에러: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"  ❌ 서버 연결 실패: {base_url}")
        print("  💡 웹 서버가 실행 중인지 확인하세요:")
        print("     python portfolio_web_app.py --env demo --port 5001")
        return False
    except Exception as e:
        print(f"  ❌ 에러: {e}")
        return False


def main():
    """메인 함수"""
    print("🔍 웹 브라우저 DB 데이터 확인")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:5001"
    
    # 1. 웹 서버 상태 확인
    if not check_web_server_status(base_url):
        return False
    
    print()
    
    # 2. API 테스트
    api_success = test_web_api(base_url)
    
    if api_success:
        print("\n🎉 모든 준비 완료!")
        print(f"🌐 웹 브라우저에서 {base_url} 접속")
        print("📋 체크리스트:")
        print("  1. 🗄️ '데이터베이스' 탭 클릭")
        print("  2. 💰 '거래 기록' 서브탭에서 15건 데이터 확인") 
        print("  3. ⚖️ '리밸런싱 로그' 서브탭에서 3건 데이터 확인")
        print("  4. 📊 '포트폴리오 스냅샷' 서브탭에서 10건 데이터 확인")
        print("  5. 📋 '시스템 로그' 서브탭에서 21건 데이터 확인")
        print("  6. 🔍 각 탭에서 필터링 및 리셋 버튼 테스트")
        print("  7. 📄 페이지네이션 (이전/다음) 버튼 테스트")
    else:
        print("\n⚠️ 문제가 발생했습니다.")
        print("🔧 확인할 사항:")
        print("  1. 웹 서버가 실행 중인지 확인")
        print("  2. 데이터베이스 서비스 상태 확인")  
        print("  3. insert_test_data.py로 테스트 데이터 재생성")
    
    return api_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)