#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
kis_auth.py 수정사항 영향도 점검 스크립트
"""

import sys
import os
from pathlib import Path

# 모듈 경로 추가
modules_path = Path(__file__).parent / "modules"
sys.path.insert(0, str(modules_path))

from kis_auth import KISAuth

def test_tr_id_conversion():
    """TR_ID 변환 로직을 테스트합니다.""" 
    # 가짜 설정으로 KISAuth 인스턴스 생성
    auth_real = KISAuth("dummy", "dummy", "12345678", "01", "", "real")
    auth_demo = KISAuth("dummy", "dummy", "12345678", "01", "", "demo")
    
    # 가짜 토큰 설정 (인증 없이 테스트하기 위해)
    auth_real.token = "fake_token"
    auth_demo.token = "fake_token"
    
    test_tr_ids = [
        "CTRP6504R",    # 계좌 잔고 조회 (C로 시작)
        "CTCA0903R",    # 휴일 조회 (C로 시작) 
        "CTPF1114R",    # 채권 정보 조회 (CTPF로 시작)
        "TTTC8434R",    # T로 시작
        "FHKST01010100", # F로 시작
        "H0STCNT0"      # H로 시작
    ]
    
    print("=" * 70)
    print("TR_ID 변환 테스트 결과")
    print("=" * 70)
    print(f"{'TR_ID':<15} {'실전투자':<15} {'모의투자':<15} {'영향':<10}")
    print("-" * 70)
    
    for tr_id in test_tr_ids:
        # 실전투자 헤더
        real_headers = auth_real.get_headers(tr_id)
        real_tr_id = real_headers.get('tr_id', tr_id)
        
        # 모의투자 헤더
        demo_headers = auth_demo.get_headers(tr_id)
        demo_tr_id = demo_headers.get('tr_id', tr_id)
        
        # 영향도 판단
        impact = "변경됨" if real_tr_id != demo_tr_id else "동일"
        
        print(f"{tr_id:<15} {real_tr_id:<15} {demo_tr_id:<15} {impact:<10}")
    
    print("=" * 70)
    
    # 수정사항 영향 분석
    print("\n수정사항 영향 분석:")
    print("- 이전: C로 시작하는 모든 TR_ID가 모의투자에서 V로 변환")
    print("- 현재: CTPF로 시작하는 TR_ID는 변환하지 않음")
    print("- 영향: CTRP6504R, CTCA0903R 등은 더 이상 변환되지 않음")
    print("- 주의: 이들 API가 모의투자에서 지원되지 않을 수 있음")


if __name__ == "__main__":
    test_tr_id_conversion()