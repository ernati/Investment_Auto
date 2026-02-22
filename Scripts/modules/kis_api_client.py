# -*- coding: utf-8 -*-
"""
KIS API Client Module
한국투자증권 Open Trading API 클라이언트
"""

import requests
import pandas as pd
from typing import Optional, Dict, Any


class KISAPIClient:
    """한국투자증권 API 클라이언트 클래스"""
    
    # 주요 종목코드 매핑 (종목명 조회용)
    STOCK_NAMES = {
        "005930": "삼성전자",
        "000660": "SK하이닉스",
        "035420": "NAVER",
        "035720": "카카오",
        "373220": "LG에너지솔루션",
        "207940": "삼성바이오로직스",
        "006400": "삼성SDI",
        "005380": "현대차",
        "000270": "기아",
        "005490": "POSCO홀딩스",
    }
    
    def __init__(self, auth):
        """
        Args:
            auth: KISAuth 인증 객체
        """
        self.auth = auth
        
    def _call_api(self, endpoint, tr_id, params=None, method='GET', tr_cont=""):
        """API를 호출합니다.
        
        Args:
            endpoint (str): API 엔드포인트
            tr_id (str): 거래ID
            params (dict): 요청 파라미터
            method (str): HTTP 메서드 ('GET' 또는 'POST')
            tr_cont (str): 연속조회 여부
            
        Returns:
            dict: API 응답
        """
        url = f"{self.auth.base_url}{endpoint}"
        headers = self.auth.get_headers(tr_id, tr_cont)
        
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        else:  # POST
            response = requests.post(url, headers=headers, json=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API 호출 실패: {response.status_code}, {response.text}")
    
    def inquire_price(self, stock_code, market_code="J"):
        """주식 현재가를 조회합니다.
        
        Args:
            stock_code (str): 종목코드 (예: "005930")
            market_code (str): 시장구분코드 (J:KRX, NX:NXT, UN:통합)
            
        Returns:
            pd.DataFrame: 현재가 정보
        """
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"
        tr_id = "FHKST01010100"
        
        params = {
            "FID_COND_MRKT_DIV_CODE": market_code,
            "FID_INPUT_ISCD": stock_code
        }
        
        response = self._call_api(endpoint, tr_id, params)
        
        if response['rt_cd'] == '0':
            # 정상 응답
            output = response['output']
            df = pd.DataFrame([output])
            return df
        else:
            # 오류 응답
            raise Exception(f"API 오류: [{response['msg_cd']}] {response['msg1']}")
    
    def get_market_price(self, stock_code, market_code="J"):
        """시장가 정보를 조회합니다. (현재가 조회의 별칭)
        
        Args:
            stock_code (str): 종목코드
            market_code (str): 시장구분코드
            
        Returns:
            dict: 주요 시장가 정보
        """
        df = self.inquire_price(stock_code, market_code)
        
        if df.empty:
            return None
        
        # 주요 정보만 추출
        data = df.iloc[0]
        
        # 종목명 가져오기 (매핑에서 찾거나 업종명 사용)
        stock_name = self.STOCK_NAMES.get(stock_code, data.get('bstp_kor_isnm', ''))
        
        result = {
            '종목코드': stock_code,
            '종목명': stock_name,
            '현재가': data.get('stck_prpr', ''),
            '전일대비': data.get('prdy_vrss', ''),
            '등락률': data.get('prdy_ctrt', ''),
            '시가': data.get('stck_oprc', ''),
            '고가': data.get('stck_hgpr', ''),
            '저가': data.get('stck_lwpr', ''),
            '거래량': data.get('acml_vol', ''),
            '거래대금': data.get('acml_tr_pbmn', ''),
        }
        
        return result
