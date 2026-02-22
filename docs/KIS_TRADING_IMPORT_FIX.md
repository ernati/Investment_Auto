# KIS Trading Import 문제 해결 가이드

## 문제 상황
```
ImportError: attempted relative import with no known parent package
```

Investment_Auto 저장소의 스크립트 실행 시 발생하는 모듈 import 오류 해결 방법을 설명합니다.

## 주요 해결 방법

### 1. 패키지 구조 정규화

**Scripts/__init__.py** 생성:
```python
# -*- coding: utf-8 -*-
"""
Investment Auto Trading Scripts Package
한국투자증권 자동 투자 스크립트 패키지
"""

__version__ = '1.0.0'
```

**Scripts/modules/__init__.py** 생성:
```python
# -*- coding: utf-8 -*-
"""
Investment Auto Trading Modules Package
한국투자증권 자동 투자 관련 모듈들
"""

# 기본 모듈들만 import (필요시 추가)
try:
    from kis_auth import KISAuth
    from kis_api_utils import build_api_headers, execute_api_request_with_retry
    from kis_trading import KISTrading
    from config_loader import PortfolioConfigLoader
    from config_validator import ConfigValidator
except ImportError as e:
    # 개별 모듈 import 실패 시 경고만 출력
    import warnings
    warnings.warn(f"Some modules could not be imported: {e}")

__version__ = '1.0.0'
```

### 2. 상대 import를 절대 import로 변경

**변경 전:**
```python
from .kis_api_utils import execute_api_request_with_retry, build_api_headers
from .kis_auth import KISAuth
```

**변경 후:**
```python
from kis_api_utils import execute_api_request_with_retry, build_api_headers
from kis_auth import KISAuth
```

### 3. 애플리케이션 스크립트 수정

**samsung_auto_trading.py**:
```python
# 상위 Scripts 디렉토리를 패키지 경로에 추가
scripts_path = str(Path(__file__).parent.parent)
if scripts_path not in sys.path:
    sys.path.insert(0, scripts_path)

from modules.kis_app_utils import (
    setup_kis_trading_client,
    print_separator,
    print_info,
    handle_common_errors
)
```

### 4. Logging 시스템 보완

**kis_trading.py**:
```python
import logging
import pandas as pd
from typing import Optional, Dict, Any

from kis_api_utils import execute_api_request_with_retry, build_api_headers

logger = logging.getLogger(__name__)
```

## 수정된 파일 목록

- `Scripts/__init__.py` (신규)
- `Scripts/modules/__init__.py` (신규)
- `Scripts/modules/kis_trading.py` (수정)
- `Scripts/modules/kis_api_utils.py` (수정)
- `Scripts/modules/kis_diagnostic.py` (수정)
- `Scripts/modules/kis_portfolio_fetcher.py` (수정)
- `Scripts/modules/rebalancing_engine.py` (수정)
- `Scripts/modules/scheduler.py` (수정)
- `Scripts/modules/order_executor.py` (수정)
- `Scripts/modules/config_validator.py` (수정)
- `Scripts/apps/samsung_auto_trading.py` (수정)

## 테스트 방법

```bash
cd d:\dev\repos\Investment_Auto
python Scripts\apps\samsung_auto_trading.py --demo
```

## 추가 주의사항

1. **주식 거래 시간**: 주말이나 장외 시간에는 `모의투자 영업일이 아닙니다` 오류가 정상적으로 발생합니다.
2. **설정 파일**: `Config/config.json`에 올바른 API 키가 설정되어 있어야 합니다.
3. **패키지 구조**: 다른 앱에서도 같은 import 방식을 사용하면 됩니다.

## 결과

- ✅ Import 오류 완전 해결
- ✅ API 설정 로드 및 인증 성공  
- ✅ 주식 현재가 조회 성공
- ✅ 거래 API 호출 가능 (영업시간 내)