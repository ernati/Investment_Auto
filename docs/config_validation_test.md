# Config Validation Test 문서

## 개요
config_validation_test.py는 Investment_Auto 프로젝트의 설정 파일 구조 개선과 검증 기능을 테스트하는 스크립트입니다. 새롭게 도입된 카테고리별 자산 관리 구조와 비율 합계 검증 기능의 정상 작동을 확인합니다.

## 주요 기능

### 1. 설정 구조 개선
- **기존 구조**: 모든 자산을 target_weights 하나의 키에 평면적으로 관리
- **개선된 구조**: 자산을 카테고리별(주식, 채권 등)로 구분하여 관리

```json
// 기존 구조
"target_weights": {
  "005930": 0.40,
  "000660": 0.25,
  "035420": 0.25,
  "KR6095572D81": 0.10
}

// 개선된 구조  
"target_weights": {
  "stocks": {
    "005930": 0.40,
    "000660": 0.25,
    "035420": 0.25
  },
  "bonds": {
    "KR6095572D81": 0.10
  }
}
```

### 2. 비율 합계 검증
- 모든 자산의 비중 합계가 1.0(100%)인지 자동 검증
- 오차 허용 범위: 1e-6 (소수점 6자리)
- 합계가 1.0이 아닌 경우 오류 로그 출력 후 프로그램 종료

### 3. 지원하는 자산 카테고리
- `stocks`: 주식
- `bonds`: 채권  
- `etfs`: 상장지수펀드
- `reits`: 리츠
- `commodities`: 원자재
- `crypto`: 암호화폐

## 테스트 시나리오

### 1. 정상 설정 테스트 (`test_config_loading_and_validation`)
- 설정 파일 로딩 검증
- 새로운 target_weights 구조 확인
- 카테고리별 자산 분석
- 비율 합계 검증
- ConfigValidator를 통한 전체 검증

### 2. 오류 설정 테스트 (`test_invalid_config`)
- 의도적으로 비율 합계를 1.0이 아닌 값(예: 1.1)으로 설정
- 검증 기능이 올바르게 오류를 감지하는지 확인
- 원본 설정 파일 보호를 위한 임시 파일 사용

## 출력 정보

### 카테고리별 분석
각 자산 카테고리에 대해 다음 정보를 출력합니다:
- 자산 수
- 카테고리별 비중 합계
- 개별 자산별 비중

### 검증 결과
- 전체 비중 합계
- 오류 목록 (있는 경우)
- 경고 목록 (있는 경우)
- 검증 성공/실패 여부

## 사용 방법

```bash
cd d:\dev\repos\Investment_Auto\Scripts\apps
python config_validation_test.py
```

## 의존성
- `config_loader.PortfolioConfigLoader`: 설정 파일 로딩
- `config_validator.ConfigValidator`: 설정 검증
- `json`: JSON 파일 처리
- `pathlib`: 파일 경로 처리

## 관련 파일 수정사항

### 1. config_validator.py
- `_validate_target_weights()` 메소드를 중첩 구조에 맞게 완전히 재작성
- 카테고리별 검증 로직 추가
- 지원되지 않는 카테고리에 대한 경고 기능

### 2. config_loader.py  
- `_print_config_summary()` 메소드를 중첩 구조에 맞게 수정
- 카테고리별 자산 수 계산 및 출력

### 3. rebalancing_engine.py
- `_flatten_target_weights()` 메소드 추가
- 중첩된 구조를 평면적인 딕셔너리로 변환하는 기능

### 4. portfolio_rebalancing.py
- target_weights에서 모든 ticker를 추출하는 로직 수정
- 중첩 구조를 고려한 ticker 리스트 생성

## 로깅 레벨
- `INFO`: 일반적인 진행 상황
- `DEBUG`: 상세한 디버깅 정보 (평면화된 target_weights 등)
- `WARNING`: 경고사항 (지원되지 않는 카테고리 등)
- `ERROR`: 오류 상황 (비율 합계 오류 등)

## 주의사항
1. 테스트 실행 시 원본 설정 파일은 임시로 백업되어 보호됩니다
2. 테스트 실패 시에도 원본 설정 파일이 복구됩니다
3. 비율 합계는 반드시 정확히 1.0이어야 하며, 소수점 오차도 허용하지 않습니다

## 개선 효과
- **가독성 향상**: 자산을 카테고리별로 구분하여 한눈에 파악 가능
- **관리 편의성**: 주식, 채권 등 자산군별로 체계적 관리
- **오류 방지**: 자동 검증으로 설정 오류 사전 방지
- **확장성**: 새로운 자산 카테고리 쉽게 추가 가능