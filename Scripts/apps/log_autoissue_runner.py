"""
log_autoissue_runner.py

k3s Pod 로그 수집 → 에러 분석 → GitHub Issue 생성 → Copilot Agent 할당
전체 파이프라인을 실행하는 엔트리포인트 스크립트.

환경변수:
    LOG_NAMESPACE           - 대상 Kubernetes namespace (필수)
    LOG_LABEL_SELECTOR      - Pod 선택 label selector (필수, 예: "app=my-service")
    GITHUB_TOKEN            - GitHub Personal Access Token 또는 App 토큰 (필수)
    GITHUB_REPO             - 대상 GitHub 저장소 (필수, 예: "owner/repo")
    COPILOT_AGENT_USERNAME  - Copilot Coding Agent GitHub 사용자명 (선택)
    MAX_ISSUES_PER_RUN      - 실행 당 최대 Issue 생성 수 (기본값 5)
"""

import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)


def _load_env() -> dict:
    """필수 환경변수를 로드하고 누락 시 오류를 발생시킨다."""
    required = {
        "LOG_NAMESPACE": os.environ.get("LOG_NAMESPACE", ""),
        "LOG_LABEL_SELECTOR": os.environ.get("LOG_LABEL_SELECTOR", ""),
        "GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", ""),
        "GITHUB_REPO": os.environ.get("GITHUB_REPO", ""),
    }

    missing = [key for key, val in required.items() if not val]
    if missing:
        logger.error("필수 환경변수가 설정되지 않았습니다: %s", ", ".join(missing))
        sys.exit(1)

    optional = {
        "COPILOT_AGENT_USERNAME": os.environ.get("COPILOT_AGENT_USERNAME", ""),
        "MAX_ISSUES_PER_RUN": os.environ.get("MAX_ISSUES_PER_RUN", "5"),
    }

    env = {**required, **optional}
    logger.info(
        "환경변수 로드 완료 — namespace=%s, label_selector=%s, repo=%s, "
        "copilot_agent=%s, max_issues=%s",
        env["LOG_NAMESPACE"],
        env["LOG_LABEL_SELECTOR"],
        env["GITHUB_REPO"],
        env["COPILOT_AGENT_USERNAME"] or "(미설정)",
        env["MAX_ISSUES_PER_RUN"],
    )
    return env


def run_pipeline(env: dict) -> None:
    """collect → analyze → create_issues → assign 파이프라인을 실행한다."""
    from Scripts.modules.log_collector import collect_pod_logs
    from Scripts.modules.log_analyzer import build_bug_candidates
    from Scripts.modules.github_issue_creator import GitHubIssueCreator

    # 1. 로그 수집
    logger.info("=== [1/4] Pod 로그 수집 시작 ===")
    pod_logs = collect_pod_logs(
        namespace=env["LOG_NAMESPACE"],
        label_selector=env["LOG_LABEL_SELECTOR"],
    )
    if not pod_logs:
        logger.info("수집된 로그가 없습니다. 파이프라인을 종료합니다.")
        return
    logger.info("로그 수집 완료: %d개 Pod", len(pod_logs))

    # 2. 에러 분석 및 버그 후보 생성
    logger.info("=== [2/4] 에러 분석 및 버그 후보 추출 시작 ===")
    bug_candidates = build_bug_candidates(pod_logs)
    if not bug_candidates:
        logger.info("버그 후보가 없습니다. 파이프라인을 종료합니다.")
        return
    logger.info("버그 후보 %d개 추출", len(bug_candidates))

    # 3. GitHub Issue 생성
    logger.info("=== [3/4] GitHub Issue 생성 시작 ===")
    creator = GitHubIssueCreator(
        token=env["GITHUB_TOKEN"],
        repo_name=env["GITHUB_REPO"],
    )
    creator.reset_run_counter()

    created_issues = []
    for candidate in bug_candidates:
        issue = creator.create_issue(candidate)
        if issue is not None:
            created_issues.append((issue, candidate))

    logger.info("Issue 생성 완료: %d개", len(created_issues))

    # 4. Copilot Agent 할당
    if not created_issues:
        logger.info("생성된 Issue가 없으므로 할당 단계를 건너뜁니다.")
        return

    logger.info("=== [4/4] Copilot Agent 할당 시작 ===")
    copilot_username = env.get("COPILOT_AGENT_USERNAME", "")
    assigned_count = 0
    for issue, _ in created_issues:
        success = creator.assign_copilot_agent(issue, username=copilot_username)
        if success:
            assigned_count += 1

    logger.info(
        "파이프라인 완료 — Issue 생성: %d개, Copilot 할당: %d개",
        len(created_issues),
        assigned_count,
    )


def main() -> None:
    """스크립트 진입점."""
    logger.info("k3s-log-copilot-autoissue 파이프라인 시작")
    env = _load_env()
    run_pipeline(env)
    logger.info("파이프라인 종료")


if __name__ == "__main__":
    main()
