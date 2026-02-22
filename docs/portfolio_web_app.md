# Portfolio Web App (포트폴리오 웹 애플리케이션)

## 개요
Portfolio Web App은 Investment_Auto 프로젝트에서 독립적으로 실행할 수 있는 웹 애플리케이션으로, 포트폴리오 현황을 브라우저에서 실시간으로 모니터링할 수 있는 기능을 제공합니다.

## 특징
- **독립 실행**: portfolio_rebalancing.py 없이도 단독으로 실행 가능
- **실시간 모니터링**: 계좌 정보와 보유 자산을 실시간으로 확인
- **환경별 지원**: demo(모의투자)와 real(실전투자) 환경 지원  
- **안전한 접근**: 기본적으로 로컬호스트에서만 접근 가능

## 파일 위치
```
Investment_Auto/
├── Scripts/
│   ├── apps/
│   │   └── portfolio_web_app.py  # 메인 애플리케이션 파일
│   ├── modules/
│   │   └── web_server.py         # 웹 서버 모듈 
│   └── templates/
│       └── portfolio.html        # 웹 페이지 템플릿
```

## 실행 방법

### 기본 실행 (Demo 환경)
```bash
cd d:\dev\repos\Investment_Auto\Scripts\apps
python portfolio_web_app.py
```

기본 설정:
- 포트: 5000
- 호스트: 127.0.0.1 (localhost)
- 환경: demo (모의투자)

웹 브라우저에서 `http://127.0.0.1:5000` 접속

### 옵션을 사용한 실행

#### 1. 사용자 정의 포트
```bash
python portfolio_web_app.py --port 8080
```

#### 2. 실전 투자 환경
```bash
python portfolio_web_app.py --env real
```

#### 3. 종합 옵션
```bash
python portfolio_web_app.py --port 8080 --host 0.0.0.0 --env demo
```

⚠️ **주의**: `--host 0.0.0.0`은 외부에서도 접근 가능하게 하므로 보안에 주의하세요.

## 명령줄 옵션

### 전체 옵션 목록
```bash
python portfolio_web_app.py --help
```

### 옵션 설명
- `--port` : 웹 서버 포트 번호 (기본값: 5000)
- `--host` : 서버 바인드 주소 (기본값: 127.0.0.1)
- `--env` : 투자 환경 설정
  - `demo`: 모의투자 환경 (기본값)
  - `real`: 실전투자 환경

## 실행 예제

### 1. 개발/테스트용 (Demo)
```bash
# 기본 설정으로 실행
python portfolio_web_app.py

# 다른 포트로 실행 (포트 충돌 시)
python portfolio_web_app.py --port 5001
```

### 2. 실전 모니터링용
```bash
# REAL 환경에서 포트폴리오 모니터링
python portfolio_web_app.py --env real --port 8080
```

### 3. 여러 환경 동시 실행
```bash
# Demo 환경 - 포트 5000
python portfolio_web_app.py --env demo --port 5000

# Real 환경 - 포트 5001 (다른 터미널에서)  
python portfolio_web_app.py --env real --port 5001
```

## 주요 클래스 및 메서드

### PortfolioWebApp 클래스
```python
class PortfolioWebApp:
    def __init__(self, port: int = 5000, host: str = "127.0.0.1", env: str = "demo")
    def start(self)  # 애플리케이션 시작
    def stop()   # 애플리케이션 중지  
    def is_running(self) -> bool  # 실행 상태 확인
```

### 시그널 처리
- `Ctrl+C` 또는 `SIGTERM`: 안전한 종료
- 웹 서버 자동 정리

## 로그 파일
애플리케이션 실행 시 로그가 기록됩니다:

```bash
portfolio_web.log  # 웹 애플리케이션 로그
```

로그 레벨: INFO
로그 형식: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

## 웹 페이지 기능

### 대시보드 구성요소
1. **헤더**: 환경 표시 (DEMO/REAL)
2. **요약 카드**: 
   - 총 자산
   - 현금
   - 주식 평가액 
   - 보유 종목 수
3. **자산 배분 차트**: 파이 차트로 비율 시각화
4. **보유 종목 테이블**: 상세 종목 정보

### 자동 기능
- **자동 새로고침**: 30초마다 데이터 업데이트
- **실시간 시계**: 마지막 업데이트 시간 표시
- **오류 처리**: API 연결 실패 시 사용자 친화적 오류 메시지

## 사용 시나리오

### 1. 일반적인 포트폴리오 모니터링
```bash
# Demo 환경에서 포트폴리오 현황 확인
python portfolio_web_app.py --env demo

# 브라우저에서 http://127.0.0.1:5000 접속
# 30초마다 자동으로 데이터 새로고침
```

### 2. 실전 투자 모니터링
```bash
# Real 환경에서 실시간 자산 추적
python portfolio_web_app.py --env real --port 8080

# 보안을 위해 localhost에서만 접근
```

### 3. 개발/디버깅
```bash
# 연결 테스트 및 디버깅
python kis_debug.py  # 웹 서버 테스트 포함

# 별도 포트로 개발 서버 실행
python portfolio_web_app.py --port 3000
```

## 보안 권장사항

### 1. 네트워크 접근 제한
```bash
# 로컬호스트만 접근 (기본값)
python portfolio_web_app.py --host 127.0.0.1

# 외부 접근이 필요한 경우 방화벽 설정
python portfolio_web_app.py --host 0.0.0.0 --port 8080
```

### 2. 환경 분리
- Demo 환경: 개발 및 테스트
- Real 환경: 실전 투자 (신중히 사용)

### 3. 포트 관리
- 기본 포트(5000) 외에 사용자 정의 포트 권장
- 방화벽에서 필요한 포트만 개방

## 문제 해결

### 1. 포트 사용 중 오류
```bash
OSError: [WinError 10048] 각 소켓 주소에 대해 하나의 사용만 허용됩니다.

# 해결방법: 다른 포트 사용
python portfolio_web_app.py --port 5001
```

### 2. KIS API 연결 실패
```bash
# 설정 검증
python kis_debug.py

# config.json 확인
# APPKEY, APPSECRET, 계좌번호 등 확인
```

### 3. 모듈 import 오류
```bash
# 의존성 설치
pip install -r requirements.txt

# Flask 재설치
pip install --upgrade Flask
```

## 연관 파일
- `web_server.py`: 웹 서버 코어 모듈
- `portfolio.html`: 웹 페이지 템플릿
- `portfolio_rebalancing.py`: 통합 실행 시 사용
- `kis_debug.py`: 디버깅 및 테스트 도구

## 업데이트 기록
- 2026-02-20: 초기 버전 생성
- 독립 실행형 웹 애플리케이션 구현
- 명령줄 인자 처리 추가
- 시그널 핸들러를 통한 안전한 종료 구현