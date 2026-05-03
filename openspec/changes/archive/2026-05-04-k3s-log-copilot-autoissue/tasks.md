## 1. 프로젝트 구조 및 의존성 설정

- [x] 1.1 `Scripts/modules/log_collector.py` 파일 생성 (스켈레톤)
- [x] 1.2 `Scripts/modules/log_analyzer.py` 파일 생성 (스켈레톤)
- [x] 1.3 `Scripts/modules/github_issue_creator.py` 파일 생성 (스켈레톤)
- [x] 1.4 `requirements.txt` 또는 `pyproject.toml`에 `PyGitHub` 의존성 추가
- [x] 1.5 `k8s/log-collector/` 디렉토리 생성

## 2. 로그 수집 컴포넌트 구현 (k3s-log-collector)

- [x] 2.1 `log_collector.py`에 `collect_pod_logs(namespace, label_selector)` 함수 구현
- [x] 2.2 kubectl API(또는 kubernetes Python 클라이언트)로 대상 Pod 목록 조회
- [x] 2.3 각 Pod의 최근 로그 조회 (실패 시 건너뛰고 로그 기록)
- [x] 2.4 수집 결과를 `{pod_name: log_text}` 딕셔너리로 반환

## 3. 로그 필터링·분석 컴포넌트 구현 (log-filter-analyzer)

- [x] 3.1 `log_analyzer.py`에 에러 키워드 패턴 정의 (`ERROR`, `CRITICAL`, `Traceback`, `Exception`, `FATAL`)
- [x] 3.2 `extract_error_blocks(log_text, context_lines=5)` 함수 구현 (전후 컨텍스트 포함 추출)
- [x] 3.3 동일 에러 패턴 중복 제거 로직 구현
- [x] 3.4 버그 후보 구조체 `{title, error_message, log_context, pod_name, occurred_at}` 생성 함수 구현
- [x] 3.5 에러 없는 경우 빈 리스트 반환 처리

## 4. GitHub Issue 자동 생성 컴포넌트 구현 (github-issue-auto-creator)

- [x] 4.1 `github_issue_creator.py`에 `GitHubIssueCreator` 클래스 구현 (PyGitHub 사용)
- [x] 4.2 `create_issue(bug_candidate)` 메서드 구현 (제목: `[AutoBug] <요약>`, 본문 포맷 포함)
- [x] 4.3 중복 Issue 확인 로직 구현 (동일 제목의 open Issue 존재 시 건너뜀)
- [x] 4.4 `MAX_ISSUES_PER_RUN` 환경변수 적용 (기본값 5)
- [x] 4.5 API 호출 실패 시 로그 기록 후 다음 후보 계속 처리

## 5. Copilot Agent 할당 컴포넌트 구현 (copilot-agent-assigner)

- [x] 5.1 `github_issue_creator.py`에 `assign_copilot_agent(issue, username)` 메서드 추가
- [x] 5.2 `COPILOT_AGENT_USERNAME` 환경변수 미설정 시 할당 건너뜀 처리
- [x] 5.3 할당 API 실패 시 로그 기록 후 파이프라인 계속 진행

## 6. 파이프라인 엔트리포인트 스크립트

- [x] 6.1 `Scripts/apps/log_autoissue_runner.py` 생성 (전체 파이프라인 실행 스크립트)
- [x] 6.2 환경변수 로드: `LOG_NAMESPACE`, `LOG_LABEL_SELECTOR`, `GITHUB_TOKEN`, `GITHUB_REPO`, `COPILOT_AGENT_USERNAME`, `MAX_ISSUES_PER_RUN`
- [x] 6.3 `collect → analyze → create_issues → assign` 파이프라인 연결

## 7. k8s 매니페스트 작성

- [x] 7.1 `k8s/log-collector/serviceaccount.yaml` 작성 (ServiceAccount)
- [x] 7.2 `k8s/log-collector/clusterrole.yaml` 작성 (pods/log get 권한만)
- [x] 7.3 `k8s/log-collector/clusterrolebinding.yaml` 작성
- [x] 7.4 `k8s/log-collector/secret.yaml` 작성 (GitHub Token 등 민감 정보 - 실제 값 제외 템플릿만)
- [x] 7.5 `k8s/log-collector/cronjob.yaml` 작성 (스케줄, 환경변수, 컨테이너 이미지 정의)

## 8. 테스트

- [x] 8.1 `log_analyzer.py` 단위 테스트 작성 (에러 추출, 중복 제거, 구조체 생성)
- [x] 8.2 `github_issue_creator.py` 단위 테스트 작성 (PyGitHub mock 사용, 중복 체크, 최대 생성 수 제한)
- [x] 8.3 `log_collector.py` 단위 테스트 작성 (kubernetes 클라이언트 mock)
- [x] 8.4 전체 파이프라인 통합 테스트 (mock 환경)

## 9. 문서화

- [x] 9.1 `k8s/log-collector/README.md` 작성 (배포 방법, 환경변수 목록, 롤백 방법)
