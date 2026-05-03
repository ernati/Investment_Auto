## ADDED Requirements

### Requirement: 주기적 Pod 로그 수집
시스템은 k3s 클러스터의 지정된 namespace/label selector에 해당하는 서비스 Pod 로그를 설정된 주기(기본 24시간)마다 자동으로 수집해야 한다. 수집은 k3s CronJob으로 실행되며, 수집 대상 namespace와 label selector는 환경변수(`LOG_NAMESPACE`, `LOG_LABEL_SELECTOR`)로 설정 가능해야 한다.

#### Scenario: CronJob 스케줄 실행
- **WHEN** CronJob 스케줄이 도래하면
- **THEN** 시스템은 지정된 namespace의 label selector에 매칭되는 모든 Pod의 최근 로그를 수집한다

#### Scenario: 로그 수집 실패 처리
- **WHEN** 특정 Pod의 로그 수집이 실패하면
- **THEN** 해당 Pod는 건너뛰고 나머지 Pod 로그 수집을 계속 진행하며, 실패 사실을 로그에 기록한다

### Requirement: 최소 권한 접근
CronJob의 ServiceAccount는 Pod 로그 조회(`pods/log`)에 대한 `get` 권한만 가져야 하며, Pod/Deployment/Service 등 다른 리소스의 수정 권한을 가져서는 안 된다.

#### Scenario: 권한 범위 확인
- **WHEN** CronJob Pod가 클러스터에서 실행되면
- **THEN** ServiceAccount는 지정 namespace의 `pods/log` read 권한만 보유하고, 다른 리소스 수정 권한을 갖지 않는다

### Requirement: 수집 로그 임시 저장
수집된 로그는 다음 처리(필터링·분석) 단계로 전달하기 위해 파이프라인 내 메모리 또는 임시 파일로 전달한다. 영구 스토리지(PV 등)는 사용하지 않는다.

#### Scenario: 로그 파이프라인 전달
- **WHEN** 로그 수집이 완료되면
- **THEN** 수집된 로그 텍스트가 필터링·분석 컴포넌트로 전달된다
