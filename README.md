# Investment_Auto

한국투자증권 KIS OpenAPI를 활용한 자동 포트폴리오 리밸런싱 시스템

## 📊 새로운 기능: 웹 대시보드

포트폴리오 현황을 실시간으로 모니터링할 수 있는 웹 대시보드를 제공합니다.

### 주요 기능
- **실시간 포트폴리오 현황**: 보유 자산, 현금, 총 자산 표시
- **자산 배분 차트**: 파이 차트로 자산 비율 시각화  
- **자동 새로고침**: 30초마다 데이터 업데이트
- **모바일 지원**: 반응형 디자인

### 사용 방법

#### 독립 웹 서버 실행
```bash
cd Scripts/apps
python portfolio_web_app.py --env demo --port 5000
```

웹 브라우저에서 `http://127.0.0.1:5000` 접속

#### 포트폴리오 리밸런싱과 함께 실행  
```bash
cd Scripts/apps
python portfolio_rebalancing.py --mode schedule --demo
```

자동으로 웹 대시보드가 함께 시작됩니다.

#### 옵션
- `--env demo|real`: 모의투자/실전투자 환경 선택
- `--port 5000`: 웹 서버 포트 설정
- `--disable-web`: 웹 서버 비활성화

## 📁 프로젝트 구조

```
Investment_Auto/
├── Config/
│   ├── config.json           # KIS API 설정 (APPKEY, APPSECRET 등)
│   ├── config_basic.json     # 기본 포트폴리오 설정
│   └── config_advanced.json  # 고급 설정
├── Scripts/
│   ├── apps/
│   │   ├── portfolio_rebalancing.py  # 메인 리밸런싱 애플리케이션
│   │   ├── portfolio_web_app.py      # 독립 웹 애플리케이션 
│   │   └── kis_debug.py              # 디버깅 도구
│   ├── modules/
│   │   ├── web_server.py            # 웹 서버 모듈
│   │   ├── kis_portfolio_fetcher.py # 포트폴리오 조회
│   │   ├── rebalancing_engine.py    # 리밸런싱 엔진
│   │   └── ...
│   └── templates/
│       └── portfolio.html           # 웹 대시보드 템플릿
├── docs/                           # 상세 문서
└── requirements.txt               # Python 의존성
```

## 🚀 시작하기

1. **의존성 설치**
```bash
pip install -r requirements.txt
```

2. **설정 파일 구성**  
`Config/config.json`에 KIS API 키 설정

3. **웹 대시보드 실행 (demo)**
```bash
cd Scripts/apps
python portfolio_web_app.py --env demo
```

## 📖 상세 문서

- [웹 서버 모듈](docs/portfolio_web_server.md)
- [독립 웹 애플리케이션](docs/portfolio_web_app.md)
- [포트폴리오 리밸런싱](docs/portfolio_rebalancing.md)
- [KIS API 설정](docs/kis_auth.md)

## 🔐 보안

- 기본적으로 `localhost (127.0.0.1)`에서만 접근 가능
- 실전 투자 시 방화벽 설정 권장
- API 키는 `Config/config.json`에서 안전하게 관리

## ⚠️ 주의사항  

- **Demo 환경**: 모의투자로 안전하게 테스트 가능
- **Real 환경**: 실제 거래가 발생하므로 신중히 사용
- API 연결 상태는 웹 대시보드에서 확인 가능