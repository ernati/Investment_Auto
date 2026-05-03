"""
github_issue_creator.py

버그 후보 구조체를 기반으로 GitHub Issue를 자동 생성하고
GitHub Copilot Coding Agent를 할당하는 모듈.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from github import Github
except ImportError:
    Github = None  # type: ignore[assignment,misc]

_ISSUE_TITLE_PREFIX = "[AutoBug]"
_DEFAULT_MAX_ISSUES_PER_RUN = 5

_ISSUE_BODY_TEMPLATE = """\
## 자동 감지된 버그 보고

| 항목 | 내용 |
|------|------|
| **Pod** | `{pod_name}` |
| **발생 시각** | `{occurred_at}` |

### 에러 메시지

```
{error_message}
```

### 로그 컨텍스트

```
{log_context}
```

---
*이 Issue는 k3s-log-copilot-autoissue 파이프라인에 의해 자동 생성되었습니다.*
"""


class GitHubIssueCreator:
    """PyGitHub를 사용하여 GitHub Issue를 생성하고 관리하는 클래스."""

    def __init__(self, token: str, repo_name: str):
        """초기화.

        Args:
            token: GitHub Personal Access Token 또는 App 토큰
            repo_name: 대상 저장소 (예: "owner/repo")
        """
        if Github is None:
            raise ImportError(
                "PyGitHub 패키지가 설치되어 있지 않습니다. "
                "'pip install PyGitHub'를 실행하세요."
            )

        self._github = Github(token)
        self._repo = self._github.get_repo(repo_name)
        self._max_issues: int = int(
            os.environ.get("MAX_ISSUES_PER_RUN", _DEFAULT_MAX_ISSUES_PER_RUN)
        )
        self._created_count: int = 0

    def reset_run_counter(self) -> None:
        """실행 당 생성 카운터를 초기화한다."""
        self._created_count = 0

    def create_issue(self, bug_candidate: dict) -> Optional[object]:
        """버그 후보 구조체로 GitHub Issue를 생성한다.

        Issue 제목은 '[AutoBug] <error_message 요약>' 형식이며,
        동일 제목의 open Issue가 이미 존재하거나 MAX_ISSUES_PER_RUN 한도에
        도달한 경우 생성하지 않는다.

        Args:
            bug_candidate: {title, error_message, log_context, pod_name, occurred_at}

        Returns:
            생성된 GitHub Issue 객체, 건너뛴 경우 None.
        """
        if self._created_count >= self._max_issues:
            logger.info(
                "MAX_ISSUES_PER_RUN(%d) 한도 도달, 나머지 버그 후보를 건너뜁니다.",
                self._max_issues,
            )
            return None

        title = f"{_ISSUE_TITLE_PREFIX} {bug_candidate['title']}"

        # 중복 Issue 확인
        if self._duplicate_exists(title):
            logger.info("중복 open Issue 존재, 건너뜀: %s", title)
            return None

        body = _ISSUE_BODY_TEMPLATE.format(
            pod_name=bug_candidate.get("pod_name", "unknown"),
            occurred_at=bug_candidate.get("occurred_at", "unknown"),
            error_message=bug_candidate.get("error_message", ""),
            log_context=bug_candidate.get("log_context", ""),
        )

        try:
            issue = self._repo.create_issue(title=title, body=body)
            self._created_count += 1
            logger.info("Issue 생성 완료 (#%d): %s", issue.number, title)
            return issue
        except Exception as exc:
            logger.error("Issue 생성 실패 (%s): %s — 다음 후보로 진행", title, exc)
            return None

    def assign_copilot_agent(
        self,
        issue,
        username: Optional[str] = None,
    ) -> bool:
        """생성된 Issue에 GitHub Copilot Coding Agent를 활성화한다.

        Copilot Agent는 일반 assignee API로 지정할 수 없다. Issue 댓글에
        @copilot 멘션을 추가하는 방식으로 Copilot Agent를 활성화한다.

        COPILOT_AGENT_USERNAME 환경변수가 설정되어 있지 않거나 비어 있으면
        건너뛴다. 댓글 작성 실패 시 로그를 기록하고 False를 반환하여
        파이프라인이 계속 진행될 수 있게 한다.

        Args:
            issue: PyGitHub Issue 객체
            username: 사용하지 않음 (하위 호환성 유지용). None이면 환경변수에서 읽는다.

        Returns:
            댓글 작성 성공 시 True, 건너뛰거나 실패 시 False.
        """
        agent_username = username or os.environ.get("COPILOT_AGENT_USERNAME", "").strip()

        if not agent_username:
            logger.debug(
                "COPILOT_AGENT_USERNAME이 설정되지 않아 Copilot Agent 활성화를 건너뜁니다."
            )
            return False

        try:
            issue.create_comment(
                f"@{agent_username} 이 Issue를 분석하고 수정해 주세요."
            )
            logger.info(
                "Issue #%d에 @%s 멘션 댓글 작성 완료 — Copilot Agent 활성화",
                issue.number,
                agent_username,
            )
            return True
        except Exception as exc:
            logger.warning(
                "Issue #%d Copilot Agent 활성화 실패 (%s): %s — 파이프라인 계속 진행",
                issue.number,
                agent_username,
                exc,
            )
            return False

    def _duplicate_exists(self, title: str) -> bool:
        """동일 제목의 open Issue가 이미 존재하는지 확인한다."""
        try:
            open_issues = self._repo.get_issues(state="open")
            for issue in open_issues:
                if issue.title == title:
                    return True
            return False
        except Exception as exc:
            logger.warning("중복 Issue 확인 실패: %s — 생성 진행", exc)
            return False
