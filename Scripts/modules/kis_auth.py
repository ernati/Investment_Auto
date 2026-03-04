# -*- coding: utf-8 -*-
"""
KIS API Authentication Module
한국투자증권 Open Trading API 인증 처리 모듈
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from collections import namedtuple

import requests


class KISAuth:
    """한국투자증권 API 인증 관리 클래스"""
    
    def __init__(self, appkey, appsecret, account, product="01", htsid="", env='real'):
        """
        Args:
            appkey (str): API 앱키
            appsecret (str): API 앱시크리트
            account (str): 계좌번호 (8자리)
            product (str): 계좌상품코드 (2자리, 기본값: "01")
            htsid (str): HTS ID
            env (str): 환경 ('real' 또는 'demo')
        """
        self.appkey = appkey
        self.appsecret = appsecret
        self.account = account
        self.product = product
        self.htsid = htsid
        self.env = env
        
        # 실전투자/모의투자 도메인 설정
        if env == 'real':
            self.base_url = "https://openapi.koreainvestment.com:9443"
        else:  # demo
            self.base_url = "https://openapivts.koreainvestment.com:29443"
        
        self.token = None
        self.token_expired = None
        self.last_auth_time = None
        
        # 토큰 저장 디렉토리 설정
        self.token_dir = Path.home() / "KIS" / "config"
        self.token_dir.mkdir(parents=True, exist_ok=True)
        self.token_file = self.token_dir / f"KIS_{env}_{datetime.today().strftime('%Y%m%d')}"
        
    def _save_token(self, token, expired):
        """토큰을 파일에 저장합니다."""
        with open(self.token_file, 'w', encoding='utf-8') as f:
            f.write(f"token: {token}\n")
            f.write(f"valid-date: {expired}\n")
    
    def _read_token(self):
        """저장된 토큰을 읽어옵니다."""
        try:
            if not self.token_file.exists():
                return None
            
            with open(self.token_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    return None
                
                token = lines[0].split(': ')[1].strip()
                valid_date_str = lines[1].split(': ')[1].strip()
                
                # 토큰 만료 체크
                valid_date = datetime.strptime(valid_date_str, "%Y-%m-%d %H:%M:%S")
                now = datetime.now()
                
                if valid_date > now:
                    return token
                else:
                    return None
        except Exception as e:
            print(f"토큰 읽기 오류: {e}")
            return None
    
    def authenticate(self, force_refresh=False):
        """API 인증을 수행하고 토큰을 발급받습니다.
        
        Args:
            force_refresh (bool): 강제로 새로운 토큰을 발급받을지 여부
            
        Returns:
            str: 액세스 토큰
        """
        # 강제 갱신이 아닌 경우에만 저장된 토큰 확인
        if not force_refresh:
            saved_token = self._read_token()
            if saved_token:
                self.token = saved_token
                self.last_auth_time = datetime.now()
                return self.token
        
        # 새 토큰 발급 또는 강제 갱신
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8"
        }
        data = {
            "grant_type": "client_credentials",
            "appkey": self.appkey,
            "appsecret": self.appsecret
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                result = response.json()
                self.token = result['access_token']
                self.token_expired = result['access_token_token_expired']
                self.last_auth_time = datetime.now()
                
                # 토큰 저장
                self._save_token(self.token, self.token_expired)
                
                return self.token
            else:
                raise Exception(f"인증 실패: {response.status_code}, {response.text}")
                
        except Exception as e:
            # 토큰 발급 실패 시 기존 토큰 파일 삭제
            if self.token_file.exists():
                self.token_file.unlink()
            raise Exception(f"토큰 발급 중 오류 발생: {str(e)}")
    
    def is_token_expired(self):
        """현재 토큰의 만료 여부를 확인합니다.
        
        Returns:
            bool: 토큰이 만료되었거나 없으면 True
        """
        if not self.token or not self.token_expired:
            return True
            
        try:
            valid_date = datetime.strptime(self.token_expired, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            # 만료 5분 전부터 갱신하도록 Buffer 적용
            return (valid_date - now).total_seconds() < 300  # 5분
        except:
            return True
    
    def refresh_token_if_needed(self):
        """필요한 경우 토큰을 갱신합니다.
        
        Returns:
            bool: 토큰 갱신 여부
        """
        if self.is_token_expired():
            try:
                self.authenticate(force_refresh=True)
                return True
            except Exception as e:
                print(f"토큰 갱신 실패: {e}")
                return False
        return False
    
    def get_headers(self, tr_id, tr_cont=""):
        """API 호출에 필요한 헤더를 생성합니다.
        
        Args:
            tr_id (str): 거래ID
            tr_cont (str): 연속조회 여부
            
        Returns:
            dict: 헤더
        """
        if not self.token:
            self.authenticate()
        
        # 모의투자인 경우 TR ID 변환 (채권 정보 조회는 변환하지 않음)
        if self.env == 'demo' and tr_id[0] in ("T", "J", "C"):
            # 채권 정보 조회 API는 모의투자에서 지원하지 않으므로 변환하지 않음
            if tr_id == "CTPF1114R":  # 채권 기본정보 조회
                pass  # 변환하지 않음
            else:
                tr_id = "V" + tr_id[1:]
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8",
            "authorization": f"Bearer {self.token}",
            "appkey": self.appkey,
            "appsecret": self.appsecret,
            "tr_id": tr_id,
            "custtype": "P",
            "tr_cont": tr_cont
        }
        
        return headers
    
    def get_env_info(self):
        """환경 정보를 반환합니다.
        
        Returns:
            namedtuple: 환경 정보
        """
        EnvInfo = namedtuple('EnvInfo', ['appkey', 'appsecret', 'account', 'product', 'htsid', 'token', 'base_url', 'env'])
        return EnvInfo(
            appkey=self.appkey,
            appsecret=self.appsecret,
            account=self.account,
            product=self.product,
            htsid=self.htsid,
            token=self.token,
            base_url=self.base_url,
            env=self.env
        )
