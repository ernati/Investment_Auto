# 웹 데이터베이스 탭 데이터 출력 문제 해결 문서

## 📋 문제 개요
웹에서 데이터베이스 탭을 눌렀을 때 DB 데이터 수는 정상적으로 불러와지지만, 하단의 DB 데이터 출력이 제대로 이루어지지 않는 문제가 발생했습니다.

## 🔍 원인 분석
문제의 원인은 JavaScript의 DOM 요소 ID 생성 로직과 실제 HTML의 ID가 일치하지 않는 것이었습니다.

### 기존 문제점
- **JavaScript 코드**: `tabName.replace('-', '') + 'Table'` 방식으로 ID 생성
  - `trading-history` → `tradinghistoryTable`
  - `rebalancing-logs` → `rebalancinglogsTable`
  - `portfolio-snapshots` → `portfoliosnapshotsTable`
  - `system-logs` → `systemlogsTable`

- **실제 HTML ID**: camelCase 방식
  - `tradingHistoryTable`
  - `rebalancingLogsTable`
  - `portfolioSnapshotsTable`
  - `systemLogsTable`

### 문제의 영향
- 데이터베이스 탭에서 각 서브탭 클릭 시 테이블 데이터가 렌더링되지 않음
- JavaScript에서 `document.getElementById()`가 요소를 찾지 못함
- API는 정상 작동하나 프런트엔드에서 표시되지 않는 현상

## 🔧 해결 방법

### 수정된 파일
- **파일 경로**: `Investment_Auto/Scripts/templates/portfolio.html`
- **함수**: `loadDbTabData(tabName)`

### 수정 내용
기존 동적 ID 생성 방식을 명시적 매핑으로 변경하였습니다.

**Before:**
```javascript
const tableElement = document.getElementById(tabName.replace('-', '') + 'Table');
```

**After:**
```javascript
// Tab name to table ID mapping
const tableIdMap = {
    'trading-history': 'tradingHistoryTable',
    'rebalancing-logs': 'rebalancingLogsTable',
    'portfolio-snapshots': 'portfolioSnapshotsTable',
    'system-logs': 'systemLogsTable'
};

const tableElement = document.getElementById(tableIdMap[tabName]);
```

## ✅ 검증 결과
1. **API 테스트**: 모든 데이터베이스 API가 정상 작동 확인
2. **웹 서버 상태**: 정상 실행 중
3. **데이터베이스 연결**: 정상
4. **프런트엔드 렌더링**: 수정 후 정상 작동

## 📊 테스트 환경
- **환경**: demo
- **서버**: http://127.0.0.1:5001
- **데이터베이스**: PostgreSQL
- **포트**: 5001

## 🎯 확인 방법
웹 브라우저에서 다음 단계를 통해 정상 작동을 확인할 수 있습니다:

1. 🗄️ '데이터베이스' 탭 클릭
2. 💰 '거래 기록' 서브탭에서 데이터 표시 확인
3. ⚖️ '리밸런싱 로그' 서브탭에서 데이터 표시 확인
4. 📊 '포트폴리오 스냅샷' 서브탭에서 데이터 표시 확인
5. 📋 '시스템 로그' 서브탭에서 데이터 표시 확인
6. 🔍 필터링 및 리셋 버튼 기능 확인
7. 📄 페이지네이션 기능 확인

## 🔄 향후 개선 사항
1. HTML과 JavaScript 간 ID 명명 규칙 통일
2. 테스트 케이스 추가로 유사 문제 예방
3. 프런트엔드 오류 로깅 강화

## 📝 관련 파일
- `Scripts/templates/portfolio.html`: 웹 인터페이스 템플릿
- `Scripts/modules/web_server.py`: 웹 서버 모듈
- `Scripts/modules/db_manager.py`: 데이터베이스 관리 모듈
- `Scripts/tests/test_web_db.py`: 웹 DB 테스트 스크립트