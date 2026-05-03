"""
test_github_issue_creator.py

github_issue_creator 모듈의 단위 테스트.
PyGitHub를 mock하여 중복 체크, 최대 생성 수 제한, Copilot Agent 할당을 검증한다.
"""

import os
import pytest
from unittest.mock import MagicMock, patch


def _make_creator(token="test-token", repo="owner/repo", max_issues=5):
    """테스트용 GitHubIssueCreator 인스턴스를 생성한다."""
    mock_repo = MagicMock()
    mock_github = MagicMock()
    mock_github.get_repo.return_value = mock_repo

    with patch.dict(os.environ, {"MAX_ISSUES_PER_RUN": str(max_issues)}):
        with patch("Scripts.modules.github_issue_creator.Github", return_value=mock_github):
            from Scripts.modules.github_issue_creator import GitHubIssueCreator
            creator = GitHubIssueCreator(token=token, repo_name=repo)
    creator._repo = mock_repo
    return creator, mock_repo


def _make_candidate(title="test error", pod="pod-1"):
    return {
        "title": title,
        "error_message": "ERROR: " + title,
        "log_context": "context lines",
        "pod_name": pod,
        "occurred_at": "2024-01-01T00:00:00",
    }


class TestCreateIssue:
    def test_creates_issue_successfully(self):
        creator, mock_repo = _make_creator()
        mock_repo.get_issues.return_value = []
        mock_issue = MagicMock()
        mock_issue.number = 42
        mock_repo.create_issue.return_value = mock_issue

        result = creator.create_issue(_make_candidate())

        assert result is mock_issue
        mock_repo.create_issue.assert_called_once()
        # 제목 형식 확인
        call_kwargs = mock_repo.create_issue.call_args[1]
        assert call_kwargs["title"].startswith("[AutoBug]")

    def test_skips_duplicate_open_issue(self):
        creator, mock_repo = _make_creator()
        candidate = _make_candidate(title="dup error")
        existing_issue = MagicMock()
        existing_issue.title = "[AutoBug] dup error"
        mock_repo.get_issues.return_value = [existing_issue]

        result = creator.create_issue(candidate)

        assert result is None
        mock_repo.create_issue.assert_not_called()

    def test_respects_max_issues_per_run(self):
        creator, mock_repo = _make_creator(max_issues=2)
        mock_repo.get_issues.return_value = []
        mock_issue = MagicMock()
        mock_issue.number = 1
        mock_repo.create_issue.return_value = mock_issue

        # 3번 시도, 2번만 생성되어야 함
        results = [creator.create_issue(_make_candidate(title=f"err{i}")) for i in range(3)]

        assert results.count(None) == 1
        assert mock_repo.create_issue.call_count == 2

    def test_api_failure_returns_none(self):
        creator, mock_repo = _make_creator()
        mock_repo.get_issues.return_value = []
        mock_repo.create_issue.side_effect = Exception("API error")

        result = creator.create_issue(_make_candidate())

        assert result is None

    def test_issue_body_contains_pod_name(self):
        creator, mock_repo = _make_creator()
        mock_repo.get_issues.return_value = []
        mock_issue = MagicMock()
        mock_issue.number = 1
        mock_repo.create_issue.return_value = mock_issue

        creator.create_issue(_make_candidate(pod="my-special-pod"))

        call_kwargs = mock_repo.create_issue.call_args[1]
        assert "my-special-pod" in call_kwargs["body"]

    def test_reset_run_counter_resets_count(self):
        creator, mock_repo = _make_creator(max_issues=1)
        mock_repo.get_issues.return_value = []
        mock_issue = MagicMock()
        mock_issue.number = 1
        mock_repo.create_issue.return_value = mock_issue

        # 한도 소진
        creator.create_issue(_make_candidate(title="err1"))
        result_before_reset = creator.create_issue(_make_candidate(title="err2"))
        assert result_before_reset is None

        # 리셋 후 다시 생성 가능
        creator.reset_run_counter()
        mock_repo.create_issue.return_value = mock_issue
        result_after_reset = creator.create_issue(_make_candidate(title="err3"))
        assert result_after_reset is not None


class TestAssignCopilotAgent:
    def test_assigns_when_username_provided(self):
        creator, _ = _make_creator()
        mock_issue = MagicMock()
        mock_issue.number = 1

        result = creator.assign_copilot_agent(mock_issue, username="copilot-agent")

        assert result is True
        mock_issue.add_to_assignees.assert_called_once_with("copilot-agent")

    def test_skips_when_username_not_set(self):
        creator, _ = _make_creator()
        mock_issue = MagicMock()

        with patch.dict(os.environ, {"COPILOT_AGENT_USERNAME": ""}):
            result = creator.assign_copilot_agent(mock_issue)

        assert result is False
        mock_issue.add_to_assignees.assert_not_called()

    def test_uses_env_var_when_username_not_passed(self):
        creator, _ = _make_creator()
        mock_issue = MagicMock()
        mock_issue.number = 1

        with patch.dict(os.environ, {"COPILOT_AGENT_USERNAME": "env-agent"}):
            result = creator.assign_copilot_agent(mock_issue)

        assert result is True
        mock_issue.add_to_assignees.assert_called_once_with("env-agent")

    def test_api_failure_returns_false(self):
        creator, _ = _make_creator()
        mock_issue = MagicMock()
        mock_issue.number = 1
        mock_issue.add_to_assignees.side_effect = Exception("API error")

        result = creator.assign_copilot_agent(mock_issue, username="copilot-agent")

        assert result is False
