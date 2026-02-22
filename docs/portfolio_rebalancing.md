# Portfolio Rebalancing Application (portfolio_rebalancing.py)

## 개요
포트폴리오 리밸런싱 시스템의 메인 애플리케이션입니다.
모든 모듈을 통합하여 자동 리밸런싱을 오케스트레이션합니다.

## 최근 변경사항 (2026-02-16)

### 1. 실전투자/모의투자 모드 지원 추가
- **변경**: `--demo` 옵션 및 환경 설정 로직 추가
- **기능**: 
  - `--demo` 옵션으로 모의투자 모드 사용 가능
  - 명령줄 옵션이 설정 파일보다 우선됨
  - 환경 정보가 로그와 출력에 명확히 표시됨
- **사용법**: 
  ```bash
  # 실전투자 (기본)
  python portfolio_rebalancing.py --mode once
  
  # 모의투자  
  python portfolio_rebalancing.py --demo --mode once
  ```

## 이전 변경사항 (2026-02-08)

### 1. 스케줄 체크 우회 기능 추가
- **변경**: `--skip-schedule-check` 플래그 추가
- **목적**: once 모드에서 스케줄 규칙을 무시하고 항상 실행 가능
- **사용**: 개발/테스트 또는 수동 실행이 필요할 때 유용
- **기본값**: once 모드는 자동으로 스케줄 체크를 건너습니다 (skip_schedule_check=True로 자동 설정)

### 2. 유니코드 인코딩 문제 해결
- **문제**: Windows 콘솔에서 이모지 문자(✅, ❌, ⚠️) 출력 시 UnicodeEncodeError 발생
- **해결**: 이모지를 ASCII 호환 문자로 변경 ([OK], [ERROR], [WARNING])
- **영향**: config_validator.py의 print_report() 메서드 수정

## 주요 기능

### 1. 통합 관리
- 설정 로드 및 검증
- KIS API 인증 (Config/config.json의 키 사용)
- 포트폴리오 조회 → 리밸런싱 판단 → 주문 실행 전체 흐름
- 장 시간(09:00~15:30 KST) 확인 후 리밸런싱 수행

### 2. 실행 모드
- **Once Mode**: 한 번만 리밸런싱 사이클 실행
- **Scheduler Mode**: 지속적으로 스케줄에 따라 실행

### 3. 검증 모드
- 설정만 검증하고 종료 (`--validate-only`)

## 클래스 설명

### PortfolioRebalancingApp

#### 생성자
```python
PortfolioRebalancingApp(skip_schedule_check: bool = False, env: str = None)
```

**Parameters:**
- `skip_schedule_check` (bool, optional): 스케줄러 체크를 건너뛸지 여부. 기본값은 False입니다. 
  - `True`: run_once() 실행 시 스케줄 체크를 무시하고 항상 실행
  - `False`: 스케줄 규칙에 따라 실행 시간만 허용
- `env` (str, optional): 환경 설정 ('real' 또는 'demo'). None이면 설정 파일에서 읽음
  - `'real'`: 실전투자 모드
  - `'demo'`: 모의투자 모드  
  - `None`: 설정 파일의 kis/env 값 사용

**수행 작업:**
1. 설정 로드 및 검증
2. KIS 인증 초기화 (Config/config.json에서 env별 설정 로드)
3. 각 모듈 초기화
4. 성공/실패 여부에 따라 RuntimeError 발생

**Example:**
```python
try:
    app = PortfolioRebalancingApp()
except RuntimeError as e:
    print(f"❌ 초기화 실패: {e}")
    exit(1)
```

#### 메서드

##### run_once()
한 번의 리밸런싱 사이클을 실행합니다.

**Returns:**
- `bool`: 성공 여부

**Process:**
1. 실행 시간 확인
2. 장 시간 확인 (장 시작 전/후 또는 주말이면 스킵)
3. 포트폴리오 스냅샷 생성 (목표 종목 가격 포함)
4. 리밸런싱 계획 생성
5. 가드레일 검사
6. 주문 실행

**Return Values:**
```python
True    # 리밸런싱 실행 완료
False   # 실행 시간 아님 또는 에러 발생
```

**Example:**
```python
app = PortfolioRebalancingApp()

# 한 번 실행
success = app.run_once()
if success:
    print("✅ 리밸런싱 완료")
else:
    print("❌ 리밸런싱 미실행")
```

---

##### run_scheduler(check_interval)
스케줄러를 무한 루프로 실행합니다.

**Parameters:**
- `check_interval` (int): 체크 간격 (초, 기본값: 60)

**Behavior:**
- 지정된 간격으로 `run_once()` 호출
- 다음 실행 시간 계산 및 로깅
- Ctrl+C로 중단 가능

**Example:**
```python
app = PortfolioRebalancingApp()

# 60초마다 확인하며 무한 실행
try:
    app.run_scheduler(check_interval=60)
except KeyboardInterrupt:
    print("스케줄러 중단")
```

## 사용 방법

### 1. 한 번만 실행 (Once Mode)
```bash
python Scripts/apps/portfolio_rebalancing.py --mode once
```

**동작:**
- 설정 로드 및 검증
- 스케줄 체크: 현재 시간이 지정된 실행 시간이면 리밸런싱 수행
- 배경: 기본적으로 스케줄 규칙을 따르도록 설계됨

**스케줄 무시하고 항상 실행:**
```bash
python Scripts/apps/portfolio_rebalancing.py --mode once --skip-schedule-check
```

**동작:**
- 설정 로드 및 검증
- 스케줄 체크 무시: 항상 리밸런싱 수행
- 용도: 개발/테스트 또는 수동 실행 시 유용

### 2. 지속적 실행 (Scheduler Mode)
```bash
python Scripts/apps/portfolio_rebalancing.py --mode schedule --interval 60
```

**동작:**
- 설정 로드 및 검증
- 매 60초마다 리밸런싱 판단
- 실행 시간이면 리밸런싱 수행
- Ctrl+C로 중단될 때까지 지속

### 3. 설정만 검증
```bash
python Scripts/apps/portfolio_rebalancing.py --validate-only
```

**동작:**
- 설정 로드 및 검증
- 검증 결과 출력
- 종료 (리밸런싱 수행 안 함)

## 명령줄 인자

| 인자 | 선택 | 기본값 | 설명 |
|------|------|--------|------|
| `--mode` | O | once | 실행 모드: once 또는 schedule |
| `--interval` | O | 60 | 체크 간격 (초, schedule 모드에서만 사용) |
| `--validate-only` | O | False | 설정만 검증하고 종료 |
| `--skip-schedule-check` | O | False | 스케줄러 체크를 무시하고 실행 (once 모드에서만 효과) |

**Examples:**
```bash
# Once 모드로 한 번만 실행 (기본: 스케줄 체크함)
python portfolio_rebalancing.py --mode once

# Once 모드로 스케줄 체크 무시하고 실행
python portfolio_rebalancing.py --mode once --skip-schedule-check

# 60초마다 확인 (기본, 스케줄러 모드)
python portfolio_rebalancing.py --mode schedule

# 30초마다 확인
python portfolio_rebalancing.py --mode schedule --interval 30

# 설정만 검증
python portfolio_rebalancing.py --validate-only
```

## 실행 흐름

### Once Mode Flow
```
Application 초기화
  ├─ 설정 로드
  ├─ 설정 검증
  ├─ KIS 인증
  └─ 모듈 초기화
  ↓
한 번 실행
  ├─ 실행 시간 확인
  ├─ 포트폴리오 조회
  ├─ 계획 수립
  ├─ 가드레일 검사
  └─ 주문 실행
  ↓
완료 및 종료
```

### Scheduler Mode Flow
```
Application 초기화
  ↓
무한 루프 (Ctrl+C까지)
  ├─ 한 번 실행 (위와 동일)
  ├─ 다음 실행 시간 계산
  ├─ check_interval 대기
  └─ 반복
  ↓
중단 (Ctrl+C)
```

## 로깅

### 로그 파일
- `portfolio_rebalancing.log`: 애플리케이션 루트 디렉토리에 생성
- 모든 동작이 기록됨

### 로그 레벨
- INFO: 일반 동작 정보
- WARNING: 경고 (가드레일 미통과 등)
- ERROR: 오류 및 예외

### 로그 예시
```
2025-02-08 10:00:00 - __main__ - INFO - Starting Portfolio Rebalancing Application
2025-02-08 10:00:00 - modules.config_loader - INFO - Loaded basic config...
2025-02-08 10:00:01 - modules.config_validator - INFO - All validations passed
2025-02-08 10:00:01 - modules.kis_auth - INFO - KIS Authentication initialized
2025-02-08 10:00:05 - modules.kis_portfolio_fetcher - INFO - Portfolio snapshot created...
2025-02-08 10:00:06 - modules.rebalancing_engine - INFO - Rebalancing triggered: BAND breach
2025-02-08 10:00:07 - modules.order_executor - INFO - Plan executed successfully: 3 orders
2025-02-08 10:00:07 - __main__ - INFO - Execution recorded
```

## 에러 처리

### 초기화 실패
```
❌ Configuration validation failed

→ config_basic.json 또는 config_advanced.json 확인
→ validator.print_report() 참고
```

### 실행 중 에러
```
❌ Error in rebalancing cycle: ...

→ 로그 파일 확인
→ 네트워크/API 상태 확인
→ 스케줄러는 계속 실행 (다음 사이클에서 재시도)
```

### 토큰 만료
```
❌ Error ... token expired

→ 자동으로 새 토큰 발급
→ 재시도 (KISAuth에서 처리)
```

## 환경 설정

### KIS 환경 선택
- 기본값: `demo`
- `config_basic.json`에 `kis/env`를 지정하면 변경 가능

```json
{
    "kis": {
        "env": "demo"
    }
}
```

> `dry_run`은 주문 시뮬레이션 여부만 제어하며, KIS 환경 선택에는 사용하지 않습니다.

## 사용 시나리오

### Scenario 1: 개발 및 테스트
```bash
# 1. 설정 검증만
python Scripts/apps/portfolio_rebalancing.py --validate-only

# 2. 모의투자 계좌로 한 번 실행
python Scripts/apps/portfolio_rebalancing.py --mode once

# 3. 검증 후 스케줄러로 테스트
python Scripts/apps/portfolio_rebalancing.py --mode schedule --interval 30
```

### Scenario 2: 실전 서버 배포
```bash
# crontab에 등록 (30분마다)
*/30 * * * * /usr/bin/python /path/to/Scripts/apps/portfolio_rebalancing.py --mode once

# 또는 systemd 서비스로 실행
# systemctl start portfolio-rebalancing
# (Dockerfile에서 CMD로 실행)
```

### Scenario 3: 모니터링
```bash
# 백그라운드에서 스케줄러 실행
nohup python Scripts/apps/portfolio_rebalancing.py --mode schedule --interval 60 > rebalancing.log 2>&1 &

# 로그 실시간 확인
tail -f portfolio_rebalancing.log
```

## 설정 로드 경로

```
프로젝트 루트
├── Config/
│   ├── config_basic.json      (필수)
│   └── config_advanced.json   (선택)
└── Scripts/
    └── apps/
        └── portfolio_rebalancing.py
```

**자동 감지:** 애플리케이션이 자동으로 `Config/` 디렉토리 찾음

## 반환값

### Exit Code
```python
0       # 성공
1       # 실패 (설정 오류 또는 실행 오류)
```

### run_once() Return
```python
True    # 리밸런싱 실행됨
False   # 실행 시간 아니거나 에러 발생
```

## 성능 고려사항

### One Mode
- 실행 시간: ~5초 (포트폴리오 조회 포함)
- 메모리: ~100MB
- CPU: 무시할 수 있는 수준

### Scheduler Mode
- 체크 간격: 권장 60~300초
- 메모리: 지속적으로 누수되지 않음
- CPU: 체크 간격동안 idle

## 주의사항

### 1. 중복 실행 방지
```bash
# ❌ 동시에 여러 인스턴스 실행 금지
# → 동일 계좌에 중복 주문 가능

# ✅ 슈퍼바이저 또는 systemd로 단일 인스턴스만 실행
```

### 2. 설정 변경 시
```bash
# 설정 변경 후 스케줄러 재시작 필요
# Ctrl+C로 중단 → 다시 실행
# (run_scheduler()는 초기 설정을 캐시함)
```

### 3. Dry-run 모드
```bash
# ❌ 개발 중: 절대 dry_run=false로 테스트 금지
# ✅ 항상 dry_run=true로 검증 후 전환
```

### 4. 로그 파일
```bash
# 로그 파일이 커질 수 있음
# 주기적으로 로테이션하거나 정리 권장
```

## 문제 해결

### 문제: 설정 검증 실패
```
Solution:
1. python portfolio_rebalancing.py --validate-only 실행
2. 출력된 에러 메시지 확인
3. config_basic.json 또는 config_advanced.json 수정
4. 재실행
```

### 문제: 리밸런싱이 절대 실행되지 않음
```
Solution:
1. --validate-only로 검증 (경고 확인)
2. config_basic.json의 schedule 설정 확인
   - hourly.enabled 또는 run_times 확인
3. checker_interval 값이 작은지 확인
4. 타임존 설정 확인
```

### 문제: API 호출 실패
```
Solution:
1. KIS API 상태 확인 (openapi.koreainvestment.com)
2. 토큰 만료 (자동 갱신되어야 함)
3. 계좌번호 및 인증 정보 검증
4. 네트워크 연결 확인
```

## 로깅 설정 (고급)

### 로그 레벨 변경
```python
# main() 함수 내부 수정
logging.basicConfig(
    level=logging.DEBUG,  # INFO → DEBUG로 변경
    format='...'
)
```

### 로그 파일 경로 변경
```python
# main() 함수 내부 수정
logging.FileHandler(
    '/custom/path/rebalancing.log',  # 경로 변경
    encoding='utf-8'
)
```

## 참고: Main 함수

### 명령줄 옵션
- `--mode {once|schedule}`: 실행 모드 (필수)
- `--demo`: 모의투자 모드 사용 (선택)
- `--interval SECONDS`: 스케줄 모드 확인 간격 (기본값: 60)
- `--validate-only`: 설정 검증만 수행 (선택)
- `--skip-schedule-check`: 스케줄 체크 건너뛰기 (선택)

### 사용 예제
```bash
# 실전투자 한 번 실행
python portfolio_rebalancing.py --mode once

# 모의투자 한 번 실행  
python portfolio_rebalancing.py --demo --mode once

# 모의투자 스케줄 모드
python portfolio_rebalancing.py --demo --mode schedule

# 설정 검증만
python portfolio_rebalancing.py --validate-only

# 도움말 보기
python portfolio_rebalancing.py --help
```

### 코드 구조
```python
def main():
    parser = argparse.ArgumentParser(...)
    parser.add_argument('--demo', action='store_true', ...)  # 추가됨
    args = parser.parse_args()
    
    env = "demo" if args.demo else "real"  # 환경 설정
    
    try:
        app = PortfolioRebalancingApp(
            skip_schedule_check=skip_schedule_check,
            env=env  # 환경 전달
        )
        
        if args.validate_only:
            return 0
        
        if args.mode == 'once':
            success = app.run_once()
            return 0 if success else 1
        else:
            app.run_scheduler(check_interval=args.interval)
            return 0
    
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```
