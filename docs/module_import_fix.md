# Module Import 문제 해결 가이드

## 문제 상황

### 발생한 오류
```
D:\dev\repos\Investment_Auto\Scripts\modules\__init__.py:17: UserWarning: Some modules could not be imported: No module named 'kis_auth'
  warnings.warn(f"Some modules could not be imported: {e}")
Traceback (most recent call last):
  File "D:\dev\repos\Investment_Auto\Scripts\modules\config_validator.py", line 11, in <module>
    from config_loader import PortfolioConfigLoader
ModuleNotFoundError: No module named 'config_loader'
```

### 원인 분석
1. **절대 임포트 사용**: modules 폴더 내의 파일들이 서로를 참조할 때 절대 임포트(`from module_name import`)를 사용
2. **순환 참조 문제**: `__init__.py`에서 절대 임포트로 인한 모듈 순환 참조 발생  
3. **패키지 구조 인식 문제**: Python이 modules 폴더를 패키지로 인식하지 못함

## 해결 방법

### 1. 상대 임포트로 변경
동일한 패키지 내의 모듈들을 참조할 때는 상대 임포트(`.module_name`)를 사용하도록 수정

#### 수정된 파일들:
- `__init__.py` - 모든 내부 모듈 임포트를 상대 임포트로 변경
- `config_validator.py` - config_loader 참조를 상대 임포트로 변경
- `kis_portfolio_fetcher.py` - 내부 모듈 참조를 상대 임포트로 변경  
- `kis_trading.py` - kis_api_utils 참조를 상대 임포트로 변경
- `scheduler.py` - config_loader 참조를 상대 임포트로 변경
- `rebalancing_engine.py` - 내부 모듈 참조들을 상대 임포트로 변경
- `order_executor.py` - 내부 모듈 참조들을 상대 임포트로 변경
- `kis_api_utils.py` - kis_auth 참조를 상대 임포트로 변경
- `kis_diagnostic.py` - 내부 모듈 참조들을 상대 임포트로 변경
- `kis_app_utils.py` - 내부 모듈 참조들을 상대 임포트로 변경

#### 변경 예시:
**변경 전:**
```python
from kis_auth import KISAuth
from config_loader import PortfolioConfigLoader
from portfolio_models import PortfolioSnapshot
```

**변경 후:**
```python  
from .kis_auth import KISAuth
from .config_loader import PortfolioConfigLoader
from .portfolio_models import PortfolioSnapshot
```

### 2. __init__.py 수정
패키지 초기화 시 상대 임포트 사용으로 순환 참조 문제 해결

**변경 전:**
```python
from kis_auth import KISAuth
from config_loader import PortfolioConfigLoader
```

**변경 후:**
```python
from .kis_auth import KISAuth  
from .config_loader import PortfolioConfigLoader
```

## 확인 결과

### 실행 성공
```bash
python Scripts\apps\portfolio_rebalancing.py --demo --mode schedule
```

실행 결과:
- ✅ 모든 모듈이 정상적으로 로드됨
- ✅ 설정 파일들이 성공적으로 읽힘  
- ✅ KIS API 인증이 정상적으로 초기화됨
- ✅ 스케줄러가 정상적으로 시작됨

## 추가 권장사항

### 1. 패키지 구조 관리
- 같은 패키지 내 모듈들 간에는 상대 임포트 사용
- 외부 라이브러리나 표준 라입브러리는 절대 임포트 사용
- `__init__.py`에서 패키지 공개 인터페이스 정의

### 2. 임포트 스타일 가이드  
```python
# 표준 라이브러리
import os
import sys
from datetime import datetime

# 외부 라이브러리  
import requests
import pandas as pd

# 같은 패키지의 모듈들
from .kis_auth import KISAuth
from .config_loader import PortfolioConfigLoader
```

### 3. 순환 참조 방지
- 모듈 간 상호 의존성 최소화
- 필요시 지연 임포트(lazy import) 사용
- 공통 기능은 별도 유틸리티 모듈로 분리

## 관련 파일들
- `/Scripts/modules/__init__.py` - 패키지 초기화 파일
- `/Scripts/modules/config_validator.py` - 설정 검증 모듈
- `/Scripts/modules/kis_portfolio_fetcher.py` - 포트폴리오 조회 모듈  
- `/Scripts/modules/kis_api_utils.py` - API 유틸리티 모듈
- `/Scripts/modules/rebalancing_engine.py` - 리밸런싱 엔진 모듈
- `/Scripts/modules/order_executor.py` - 주문 실행 모듈
- `/Scripts/modules/scheduler.py` - 스케줄러 모듈
- `/Scripts/modules/kis_trading.py` - KIS 거래 모듈  
- `/Scripts/modules/kis_diagnostic.py` - 진단 모듈
- `/Scripts/modules/kis_app_utils.py` - 앱 유틸리티 모듈

## 해결 완료일
2026-02-18

## 작업자 노트
- 이 문제는 Python 패키지 구조와 임포트 메커니즘에 대한 이해 부족으로 발생
- 향후 새로운 모듈 추가 시에는 상대 임포트 사용 원칙을 준수해야 함
- 코드 리뷰 시 임포트 스타일도 체크할 것을 권장