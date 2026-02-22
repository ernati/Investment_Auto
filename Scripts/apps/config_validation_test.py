# -*- coding: utf-8 -*-
"""
Config_Validator_Test Script
설정 파일의 새로운 구조와 검증 기능을 테스트하는 스크립트
"""

import sys
import os
import logging
from pathlib import Path
import json

# Scripts/modules 경로를 Python path에 추가
SCRIPT_DIR = Path(__file__).parent
MODULES_DIR = SCRIPT_DIR.parent / "modules"  # Scripts/modules
CONFIG_DIR = SCRIPT_DIR.parent.parent / "Config"  # Investment_Auto/Config
sys.path.insert(0, str(MODULES_DIR))

from config_loader import PortfolioConfigLoader
from config_validator import ConfigValidator


def setup_logging():
    """로깅 설정"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
        ]
    )


def test_config_loading_and_validation():
    """설정 로딩과 검증 테스트"""
    print(f"\n{'='*80}")
    print(" Config 구조 개선 및 검증 테스트")
    print(f"{'='*80}")
    
    try:
        # 1. 설정 로드
        print("\n[1단계] 설정 파일 로딩...")
        config_loader = PortfolioConfigLoader()
        print("✅ 설정 로딩 성공")
        
        # 2. 새로운 target_weights 구조 출력
        print("\n[2단계] 새로운 target_weights 구조 확인...")
        target_weights = config_loader.get_basic("target_weights", {})
        print(f"Target Weights 구조:")
        print(json.dumps(target_weights, indent=2, ensure_ascii=False))
        
        # 3. 카테고리별 정보 출력
        print("\n[3단계] 카테고리별 자산 분석...")
        total_weight = 0.0
        category_summaries = {}
        
        for category, assets in target_weights.items():
            if isinstance(assets, dict):
                category_total = sum(assets.values())
                category_summaries[category] = {
                    'assets_count': len(assets),
                    'total_weight': category_total,
                    'assets': assets
                }
                total_weight += category_total
                
                print(f"\n  📊 [{category}] 카테고리:")
                print(f"    - 자산 수: {len(assets)}개")
                print(f"    - 비중 합계: {category_total:.4f} ({category_total*100:.2f}%)")
                for ticker, weight in assets.items():
                    print(f"    - {ticker}: {weight:.4f} ({weight*100:.2f}%)")
        
        print(f"\n  🎯 전체 포트폴리오:")
        print(f"    - 총 비중 합계: {total_weight:.6f}")
        print(f"    - 합계 검증: {'✅ 정상 (1.0)' if abs(total_weight - 1.0) < 1e-6 else '❌ 오류'}")
        
        # 4. 설정 검증
        print("\n[4단계] 설정 검증 실행...")
        validator = ConfigValidator(config_loader)
        is_valid, errors, warnings = validator.validate()
        
        print(f"\n  검증 결과: {'✅ 성공' if is_valid else '❌ 실패'}")
        
        if errors:
            print(f"\n  🚨 오류 ({len(errors)}개):")
            for i, error in enumerate(errors, 1):
                print(f"    {i}. {error}")
        
        if warnings:
            print(f"\n  ⚠️  경고 ({len(warnings)}개):")
            for i, warning in enumerate(warnings, 1):
                print(f"    {i}. {warning}")
        
        if is_valid:
            print(f"\n  🎉 모든 검증을 통과했습니다!")
        
        # 5. 설정 요약 출력
        print("\n[5단계] 설정 요약 출력...")
        config_loader._print_config_summary()
        
        return is_valid
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_invalid_config():
    """잘못된 설정 테스트"""
    print(f"\n{'='*80}")
    print(" 잘못된 설정에 대한 검증 테스트")
    print(f"{'='*80}")
    
    # 임시로 잘못된 설정 생성
    invalid_config = {
        "portfolio_id": "test-portfolio",
        "base_currency": "KRW",
        "target_weights": {
            "stocks": {
                "005930": 0.50,  # 50%
                "000660": 0.30   # 30%
            },
            "bonds": {
                "KR6095572D81": 0.30  # 30% -> 총합 110%로 오류
            }
        },
        "rebalance": {
            "mode": "HYBRID",
            "price_source": "last",
            "band": {
                "type": "ABS",
                "value": 0.05
            }
        },
        "trade": {
            "cash_buffer_ratio": 0.02,
            "min_order_krw": 100000
        }
    }
    
    # 임시 파일 생성
    temp_config_file = CONFIG_DIR / "config_basic_temp.json"
    original_config_file = CONFIG_DIR / "config_basic.json"
    
    try:
        # 원본 백업
        with open(original_config_file, 'r', encoding='utf-8') as f:
            original_config = f.read()
        
        # 잘못된 설정으로 임시 변경
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(invalid_config, f, indent=2, ensure_ascii=False)
        
        # 원본을 임시로 교체
        os.rename(original_config_file, str(original_config_file) + ".backup")
        os.rename(temp_config_file, original_config_file)
        
        # 검증 테스트
        config_loader = PortfolioConfigLoader()
        validator = ConfigValidator(config_loader)
        is_valid, errors, warnings = validator.validate()
        
        print(f"잘못된 설정 테스트 결과: {'❌ 예상대로 실패' if not is_valid else '⚠️  예상과 다름'}")
        
        if errors:
            print(f"\n🚨 감지된 오류들:")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
        
        # 원본 복구
        os.rename(original_config_file, temp_config_file)
        os.rename(str(original_config_file) + ".backup", original_config_file)
        os.remove(temp_config_file)
        
        return not is_valid  # 실패해야 성공적인 테스트
        
    except Exception as e:
        print(f"❌ 테스트 중 오류: {e}")
        
        # 원본 복구 시도
        try:
            if os.path.exists(str(original_config_file) + ".backup"):
                if os.path.exists(original_config_file):
                    os.remove(original_config_file)
                os.rename(str(original_config_file) + ".backup", original_config_file)
        except:
            pass
        
        return False


def main():
    """메인 함수"""
    setup_logging()
    
    print("🚀 Config 구조 개선 및 검증 기능 테스트를 시작합니다...\n")
    
    # 정상 설정 테스트
    test1_result = test_config_loading_and_validation()
    
    # 잘못된 설정 테스트
    test2_result = test_invalid_config()
    
    # 최종 결과
    print(f"\n{'='*80}")
    print(" 최종 테스트 결과")
    print(f"{'='*80}")
    print(f"정상 설정 테스트: {'✅ 성공' if test1_result else '❌ 실패'}")
    print(f"오류 설정 테스트: {'✅ 성공' if test2_result else '❌ 실패'}")
    
    overall_success = test1_result and test2_result
    print(f"\n전체 테스트: {'🎉 성공' if overall_success else '❌ 실패'}")
    
    if overall_success:
        print("\n✨ Config 구조 개선이 성공적으로 완료되었습니다!")
        print("   - 카테고리별 자산 관리 ✅")
        print("   - 비율 합계 검증 ✅")
        print("   - 오류 감지 기능 ✅")


if __name__ == "__main__":
    main()