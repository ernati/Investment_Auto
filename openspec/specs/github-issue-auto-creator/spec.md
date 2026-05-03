# github-issue-auto-creator

## 목적

버그 후보 구조체를 기반으로 GitHub 저장소에 Issue를 자동 생성하고, 중복 방지 및 생성 수 제한을 적용하는 컴포넌트.

---

## Requirements

### Requirement: GitHub Issue 자동 생성
시스템은 버그 후보 구조체를 기반으로 GitHub 저장소에 Issue를 자동 생성해야 한다. Issue 제목은 `[AutoBug] <error_message 요약>`이며, 본문에는 에러 메시지, 로그 컨텍스트, Pod명, 발생 시각을 포함한다.

#### Scenario: Issue 정상 생성
- **WHEN** 버그 후보 구조체가 입력되고 GitHub API 호출이 성공하면
- **THEN** 지정된 저장소에 정형화된 포맷의 Issue가 생성된다

#### Scenario: API 호출 실패
- **WHEN** GitHub API 호출이 실패하면
- **THEN** 시스템은 에러를 로그에 기록하고 다음 버그 후보 처리를 계속한다

### Requirement: 중복 Issue 방지
동일한 에러 패턴에 대한 Issue가 이미 open 상태로 존재하면 새 Issue를 생성하지 않아야 한다.

#### Scenario: 중복 Issue 건너뜀
- **WHEN** 생성하려는 Issue 제목과 동일한 제목의 open Issue가 이미 존재하면
- **THEN** 새 Issue를 생성하지 않고 해당 버그 후보를 건너뛴다

### Requirement: 일일 최대 생성 수 제한
한 번의 실행에서 생성되는 Issue 수는 `MAX_ISSUES_PER_RUN` 환경변수로 설정된 최댓값(기본값 5)을 초과해서는 안 된다.

#### Scenario: 최대 생성 수 초과 방지
- **WHEN** 생성 예정 Issue 수가 MAX_ISSUES_PER_RUN을 초과하면
- **THEN** 상위 MAX_ISSUES_PER_RUN 개만 생성하고 나머지는 건너뛴다
