"""
test_pipeline_integration.py

전체 파이프라인 통합 테스트 (mock 환경).
collect → analyze → create_issues → assign 흐름을 end-to-end로 검증한다.
"""

import os
import pytest
from unittest.mock import MagicMock, patch


class TestPipelineIntegration:
    """전체 파이프라인 통합 테스트."""

    def _run_pipeline(self, pod_logs, max_issues=5, copilot_username=""):
        """파이프라인을 mock 환경에서 실행하고 결과를 반환한다."""
        mock_repo = MagicMock()
        mock_issue = MagicMock()
        mock_issue.number = 1
        mock_repo.get_issues.return_value = []
        mock_repo.create_issue.return_value = mock_issue

        mock_github_instance = MagicMock()
        mock_github_instance.get_repo.return_value = mock_repo

        env = {
            "LOG_NAMESPACE": "default",
            "LOG_LABEL_SELECTOR": "app=test",
            "GITHUB_TOKEN": "test-token",
            "GITHUB_REPO": "owner/repo",
            "COPILOT_AGENT_USERNAME": copilot_username,
            "MAX_ISSUES_PER_RUN": str(max_issues),
        }

        with patch("Scripts.modules.log_collector.collect_pod_logs", return_value=pod_logs):
            with patch.dict(os.environ, env):
                with patch("Scripts.modules.github_issue_creator.Github", return_value=mock_github_instance):
                    from Scripts.modules.log_analyzer import build_bug_candidates
                    from Scripts.modules.github_issue_creator import GitHubIssueCreator

                    # 분석
                    candidates = build_bug_candidates(pod_logs)

                    # Issue 생성
                    creator = GitHubIssueCreator(
                        token=env["GITHUB_TOKEN"],
                        repo_name=env["GITHUB_REPO"],
                    )
                    creator._repo = mock_repo

                    created = []
                    for c in candidates:
                        issue = creator.create_issue(c)
                        if issue:
                            created.append(issue)

                    # 할당
                    assigned = 0
                    for issue in created:
                        if creator.assign_copilot_agent(issue, username=copilot_username):
                            assigned += 1

        return {
            "candidates": candidates,
            "created": created,
            "assigned": assigned,
            "mock_repo": mock_repo,
        }

    def test_no_errors_produces_no_issues(self):
        pod_logs = {"pod-1": "INFO everything is fine\nINFO still fine"}
        result = self._run_pipeline(pod_logs)
        assert result["candidates"] == []
        assert result["created"] == []

    def test_error_log_creates_issue(self):
        pod_logs = {"pod-1": "INFO before\nERROR something broke\nINFO after"}
        result = self._run_pipeline(pod_logs)
        assert len(result["candidates"]) >= 1
        assert len(result["created"]) >= 1
        result["mock_repo"].create_issue.assert_called()

    def test_copilot_assigned_when_username_set(self):
        pod_logs = {"pod-1": "ERROR test error"}
        result = self._run_pipeline(pod_logs, copilot_username="copilot-bot")
        assert result["assigned"] == len(result["created"])

    def test_copilot_not_assigned_when_username_empty(self):
        pod_logs = {"pod-1": "ERROR test error"}
        result = self._run_pipeline(pod_logs, copilot_username="")
        assert result["assigned"] == 0

    def test_max_issues_limit_respected(self):
        # 10개 다른 에러를 생성하되 max_issues=3으로 제한
        lines = []
        for i in range(10):
            lines.extend([f"INFO ctx{i}", f"ERROR unique error number {i} details", f"INFO after{i}"])
        pod_logs = {"pod-1": "\n".join(lines)}
        result = self._run_pipeline(pod_logs, max_issues=3)
        assert len(result["created"]) <= 3

    def test_multiple_pods_all_processed(self):
        pod_logs = {
            "pod-a": "INFO ok\nERROR error in A\nINFO ok",
            "pod-b": "INFO ok\nERROR error in B\nINFO ok",
        }
        result = self._run_pipeline(pod_logs, max_issues=10)
        pod_names = {c["pod_name"] for c in result["candidates"]}
        assert "pod-a" in pod_names
        assert "pod-b" in pod_names
