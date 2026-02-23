# Web Server 모듈 문서

## 개요

`web_server.py` 모듈은 Investment_Auto 시스템의 웹 인터페이스를 제공하는 Flask 기반 웹 서버입니다.
실시간 포트폴리오 현황 대시보드와 데이터베이스 데이터 시각화 기능을 통합한 웹 애플리케이션을 구동합니다.

## 주요 기능

### 1. 실시간 포트폴리오 대시보드
- 계좌 잔고 및 보유 종목 현황 시각화
- 자산 배분 차트 (도넛 차트)
- 실시간 가격 정보 및 평가 손익
- 자동 새로고침 (30초 간격)

### 2. 데이터베이스 모니터링
- 거래 기록 조회 및 분석
- 리밸런싱 로그 모니터링
- 포트폴리오 스냅샷 이력
- 시스템 로그 조회

### 3. 필터링 및 페이지네이션
- 다중 조건 필터링
- 페이지별 데이터 조회
- 실시간 검색 기능

## 클래스 구조

### PortfolioWebServer

포트폴리오 상태를 웹으로 표시하는 서버 클래스입니다.

#### 초기화 매개변수

| 매개변수 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `port` | int | 5000 | 웹 서버 포트 번호 |
| `host` | str | "127.0.0.1" | 서버 호스트 주소 |
| `env` | str | "demo" | 환경 설정 ('demo' 또는 'real') |

#### 주요 메서드

##### start()
웹 서버를 백그라운드 스레드에서 시작합니다.

```python
web_server = PortfolioWebServer(port=5000, host="127.0.0.1", env="demo")
web_server.start()
```

##### stop()
실행 중인 웹 서버를 중지합니다.

##### is_running() → bool
서버 실행 상태를 확인합니다.

##### get_portfolio_data() → Dict
포트폴리오 데이터를 조회하고 캐시를 적용합니다.

```python
data = web_server.get_portfolio_data()
```

##### get_system_logs(level, module, environment, limit, offset) → List[Dict]
시스템 로그를 필터링하여 조회합니다.

## API 엔드포인트

### 포트폴리오 API

#### GET /api/portfolio
현재 포트폴리오 상태 조회

**응답 예시:**
```json
{
    "timestamp": "2026-02-22T10:30:00",
    "environment": "demo",
    "account": "12345678",
    "summary": {
        "total_assets": 15000000,
        "cash": 3000000,
        "cash_ratio": 20.0,
        "total_stock_value": 12000000,
        "stock_ratio": 80.0
    },
    "positions": [
        {
            "ticker": "005930",
            "quantity": 100,
            "current_price": 75000,
            "market_value": 7500000,
            "ratio": 50.0
        }
    ]
}
```

### 데이터베이스 API

#### GET /api/db/trading-history
거래 기록 조회

**쿼리 매개변수:**
- `portfolio_id` (str): 포트폴리오 식별자
- `environment` (str): 환경 ('demo' 또는 'real')
- `order_type` (str, optional): 주문 유형 ('buy', 'sell')
- `status` (str, optional): 주문 상태 ('completed', 'failed', 'pending')
- `limit` (int): 조회 제한 수 (기본값: 20)
- `offset` (int): 오프셋 (기본값: 0)

**응답 예시:**
```json
{
    "data": [
        {
            "id": 1,
            "timestamp": "2026-02-22T09:30:00",
            "portfolio_id": "default",
            "symbol": "005930",
            "order_type": "buy",
            "quantity": 10,
            "price": 75000,
            "total_amount": 750000,
            "commission": 1500,
            "status": "completed",
            "environment": "demo"
        }
    ],
    "total": 1,
    "limit": 20,
    "offset": 0
}
```

#### GET /api/db/rebalancing-logs
리밸런싱 로그 조회

**쿼리 매개변수:**
- `portfolio_id` (str): 포트폴리오 식별자
- `environment` (str): 환경
- `status` (str, optional): 상태 ('success', 'failed', 'partial')
- `limit` (int): 조회 제한 수
- `offset` (int): 오프셋

#### GET /api/db/portfolio-snapshots
포트폴리오 스냅샷 조회

**쿼리 매개변수:**
- `portfolio_id` (str): 포트폴리오 식별자
- `environment` (str): 환경
- `limit` (int): 조회 제한 수
- `offset` (int): 오프셋

#### GET /api/db/system-logs
시스템 로그 조회

**쿼리 매개변수:**
- `environment` (str): 환경
- `level` (str, optional): 로그 레벨 ('INFO', 'WARNING', 'ERROR')
- `module` (str, optional): 모듈명 (부분 검색)
- `limit` (int): 조회 제한 수
- `offset` (int): 오프셋

### 헬스 체크 API

#### GET /health
서버 상태 확인

**응답 예시:**
```json
{
    "status": "healthy",
    "timestamp": "2026-02-22T10:30:00",
    "environment": "demo",
    "api_status": "connected",
    "db_status": "connected"
}
```

## 웹 인터페이스 구조

### 탭 구조

#### 1. 실시간 대시보드 탭
- **요약 카드**: 총 자산, 현금, 주식 평가액, 보유 종목 수
- **자산 배분 차트**: 도넛 차트로 자산 비율 시각화
- **보유 종목 테이블**: 종목별 수량, 가격, 평가 금액, 비율

#### 2. 데이터베이스 탭
- **DB 요약 카드**: 각 테이블별 데이터 건수
- **서브 탭**: 거래 기록, 리밸런싱 로그, 포트폴리오 스냅샷, 시스템 로그
- **필터 기능**: 각 탭별 맞춤형 필터
- **페이지네이션**: 페이지별 데이터 조회

### 필터 기능

#### 거래 기록 필터
- 포트폴리오 ID
- 주문 유형 (구매/판매)
- 상태 (완료/실패/대기)

#### 리밸런싱 로그 필터
- 포트폴리오 ID
- 상태 (성공/실패/부분성공)

#### 포트폴리오 스냅샷 필터
- 포트폴리오 ID

#### 시스템 로그 필터
- 로그 레벨 (INFO/WARNING/ERROR)
- 모듈명 (부분 검색)

## 의존성 모듈

### 내부 모듈
- `config_loader`: 설정 파일 로드
- `kis_auth`: KIS API 인증
- `kis_portfolio_fetcher`: 포트폴리오 데이터 조회
- `db_manager`: 데이터베이스 연결 및 쿼리

### 외부 라이브러리
- `Flask`: 웹 서버 프레임워크
- `psycopg2`: PostgreSQL 연결

## 성능 최적화

### 캐싱
- 포트폴리오 데이터: 30초 캐시
- 자동 새로고침: 브라우저에서 30초 간격

### 페이지네이션
- 기본 페이지 크기: 20건
- 오프셋 기반 페이지네이션 

### 비동기 처리
- 백그라운드 스레드에서 서버 실행
- 논블로킹 API 호출

## 설정 관리

### KIS API 설정
```json
{
    "demo": {
        "appkey": "DEMO_APPKEY",
        "appsecret": "DEMO_APPSECRET",
        "account": "DEMO_ACCOUNT",
        "product": "kis",
        "htsid": "demo"
    }
}
```

### 데이터베이스 설정
```json
{
    "database": {
        "host": "localhost",
        "port": 5432,
        "name": "appdb",
        "user": "appuser",
        "password": "temp1234"
    }
}
```

## 사용 예시

### 기본 사용법
```python
from modules.web_server import PortfolioWebServer

# 웹 서버 인스턴스 생성
server = PortfolioWebServer(port=5000, host="127.0.0.1", env="demo")

# 서버 시작
server.start()

# 서버 상태 확인
if server.is_running():
    print("웹 서버가 성공적으로 시작되었습니다.")
    print("http://127.0.0.1:5000 에서 확인하세요.")

# 포트폴리오 데이터 조회
portfolio_data = server.get_portfolio_data()
print(f"총 자산: {portfolio_data['summary']['total_assets']:,}원")

# 서버 중지
server.stop()
```

### 사용자 정의 설정
```python
# 실제 환경에서 다른 포트로 실행
server = PortfolioWebServer(
    port=8080, 
    host="0.0.0.0",  # 외부 접속 허용
    env="real"       # 실제 환경
)
server.start()
```

## 오류 처리

### KIS API 연결 실패
- API 키가 잘못된 경우
- 네트워크 연결 문제
- 계좌 정보 불일치

```python
# 오류 시 화면에 표시
{
    "error": "KIS API not available",
    "timestamp": "2026-02-22T10:30:00",
    "environment": "demo"
}
```

### 데이터베이스 연결 실패
- DB 서버 다운
- 연결 설정 오류
- 권한 문제

```python
# API 응답에 오류 메시지 포함
{
    "error": "Database not available"
}
```

### 일반적인 오류 해결방법

1. **포트 충돌**: 다른 포트 번호 사용
2. **권한 문제**: 관리자 권한으로 실행
3. **설정 파일 누락**: Config 폴더 내 설정 파일 확인
4. **의존성 누락**: requirements.txt 설치 확인

## 보안 고려사항

### 접근 제한
- 기본적으로 로컬호스트만 접근 가능
- 외부 접근 시 방화벽 설정 필요
- HTTPS 사용 권장 (프로덕션 환경)

### API 키 보안
- 설정 파일은 저장소에 커밋하지 않음
- 환경 변수 사용 권장
- 정기적인 API 키 갱신

### 데이터베이스 보안
- 강력한 패스워드 사용
- 최소 권한 원칙 적용
- 정기적인 백업

## 확장성

### 새로운 차트 추가
1. HTML 템플릿에 차트 영역 추가
2. JavaScript에 차트 렌더링 함수 구현
3. Chart.js 라이브러리 활용

### 새로운 API 엔드포인트 추가
1. `_setup_routes()` 메서드에 라우트 추가
2. 해당 데이터 조회 메서드 구현
3. 프론트엔드에서 API 호출 추가

### 추가 필터 기능
1. DB 테이블에 인덱스 추가
2. API에서 쿼리 매개변수 처리
3. 프론트엔드 필터 UI 확장

## 모니터링

### 로그 관리
- Flask 로그: 웹 서버 요청/응답 로그
- 애플리케이션 로그: portfolio_web.log
- 에러 로그: 콘솔 및 파일 출력

### 성능 모니터링
- 응답 시간 측정
- 메모리 사용량 모니터링  
- DB 쿼리 성능 분석

### 헬스 체크
```bash
# 서버 상태 확인
curl http://localhost:5000/health

# 포트폴리오 API 테스트  
curl http://localhost:5000/api/portfolio

# DB API 테스트
curl "http://localhost:5000/api/db/trading-history?limit=1"
```

## 향후 개선 사항

### 기능 개선
- Real-time WebSocket 연결
- 사용자 인증 시스템
- 다중 포트폴리오 지원
- 모바일 반응형 UI

### 성능 개선
- Redis 캐시 도입
- 데이터베이스 커넥션 풀링
- 비동기 처리 확대
- CDN 활용

### UI/UX 개선
- 다크 모드 지원
- 커스터마이징 가능한 대시보드
- 데이터 내보내기 기능
- 알림 시스템

## 관련 모듈

- `portfolio_web_app.py`: 웹 애플리케이션 메인 런처
- `db_manager.py`: 데이터베이스 연결 및 쿼리 관리
- `kis_portfolio_fetcher.py`: KIS API 포트폴리오 데이터 조회
- `config_loader.py`: 설정 파일 관리