# Portfolio Web Server (포트폴리오 웹 서버)

## 개요
Portfolio Web Server는 Investment_Auto 프로젝트에서 포트폴리오 리밸런싱 시스템의 상태를 실시간으로 웹 브라우저에서 확인할 수 있는 기능을 제공합니다.

## 주요 기능
- **실시간 포트폴리오 현황 표시**: 보유 자산, 현금, 총 자산 등을 실시간으로 확인
- **자산 비율 시각화**: 파이 차트를 통한 자산 배분 현황 표시
- **보유 종목 상세 정보**: 각 종목별 보유량, 현재가, 평가금액, 비율 표시
- **자동 새로고침**: 30초마다 자동으로 데이터 업데이트
- **환경별 지원**: demo(모의투자)와 real(실전투자) 환경 지원

## 파일 구조

### 1. web_server.py (Scripts/modules/web_server.py)
웹 서버의 핵심 모듈입니다.

**주요 클래스:**
```python
class PortfolioWebServer:
    def __init__(self, port: int = 5000, host: str = "127.0.0.1", env: str = "demo")
    def start(self)  # 웹 서버 시작
    def stop()   # 웹 서버 중지
    def get_portfolio_data(self) -> Dict  # 포트폴리오 데이터 조회
```

**주요 API 엔드포인트:**
- `GET /` : 메인 대시보드 페이지
- `GET /api/portfolio` : 포트폴리오 데이터 JSON API
- `GET /health` : 헬스 체크 API

### 2. portfolio.html (Scripts/templates/portfolio.html)
웹 대시보드의 HTML 템플릿입니다.

**주요 기능:**
- 반응형 디자인으로 모바일/데스크톱 지원
- Chart.js를 활용한 자산 배분 파이 차트
- 실시간 데이터 업데이트를 위한 JavaScript AJAX
- 깔끔한 카드 레이아웃으로 정보 표시

### 3. portfolio_web_app.py (Scripts/apps/portfolio_web_app.py)
독립 실행 가능한 웹 애플리케이션입니다.

**사용법:**
```bash
python portfolio_web_app.py --port 5000 --env demo
```

## 사용 방법

### 1. 독립 실행
```bash
cd d:\dev\repos\Investment_Auto\Scripts\apps
python portfolio_web_app.py --port 5000 --env demo
```

### 2. 포트폴리오 리밸런싱과 함께 실행
```bash
cd d:\dev\repos\Investment_Auto\Scripts\apps
python portfolio_rebalancing.py --mode schedule --demo
```
리밸런싱 시스템과 함께 자동으로 웹 서버가 시작됩니다.

### 3. 웹 서버 비활성화
웹 서버를 사용하지 않으려면:
```bash
python portfolio_rebalancing.py --mode schedule --demo --disable-web
```

## 설정 옵션

### 명령줄 옵션
- `--port` : 웹 서버 포트 번호 (기본값: 5000)
- `--host` : 서버 호스트 주소 (기본값: 127.0.0.1)  
- `--env` : 환경 설정 (demo/real, 기본값: demo)
- `--disable-web` : 웹 서버 비활성화

## API 응답 구조

### /api/portfolio
```json
{
  "timestamp": "2026-02-20T10:00:00.000Z",
  "environment": "demo",
  "account": "50162038",
  "summary": {
    "total_assets": 10000000,
    "cash": 5000000,
    "cash_ratio": 50.0,
    "total_stock_value": 5000000,
    "stock_ratio": 50.0
  },
  "positions": [
    {
      "ticker": "005930",
      "quantity": 10,
      "current_price": 75000,
      "market_value": 750000,
      "ratio": 7.5
    }
  ],
  "balance": {
    "cash": 5000000,
    "d2_cash": 0,
    "orderable_cash": 5000000
  }
}
```

## 기술 스택
- **백엔드**: Python Flask
- **프론트엔드**: HTML, CSS, JavaScript
- **차트**: Chart.js
- **스타일**: CSS Grid, Flexbox

## 보안 고려사항
- 기본적으로 localhost(127.0.0.1)에서만 접근 가능
- 실제 운영 시에는 방화벽 설정 필요
- HTTPS 설정 권장 (실전 투자 시)

## 의존성
```bash
Flask==3.1.0
Werkzeug==3.1.3
Jinja2==3.1.5
```

### 설치 방법
```bash
pip install -r requirements.txt
```

## 문제 해결

### 1. 포트 충돌
포트가 이미 사용 중인 경우:
```bash
python portfolio_web_app.py --port 5001
```

### 2. 데이터 로딩 실패  
KIS API 연결 문제가 있을 경우 kis_debug.py로 진단:
```bash
python kis_debug.py
```

### 3. 웹 서버 시작 실패
Flask 또는 의존성 문제:
```bash
pip install --upgrade Flask
```

## 디버깅
kis_debug.py에 웹 서버 테스트 기능이 추가되어 있습니다:

```python
def test_web_server(kis_auth):
    # 웹 서버 기능 테스트
    # 포트폴리오 데이터 조회 테스트  
    # 웹 서버 시작/종료 테스트
```

## 업데이트 기록
- 2026-02-20: 초기 버전 생성
- Chart.js 기반 자산 배분 차트 구현
- 자동 새로고침 기능 추가
- portfolio_rebalancing.py 통합 완료