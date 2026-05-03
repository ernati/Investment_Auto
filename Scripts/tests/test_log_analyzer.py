"""
test_log_analyzer.py

log_analyzer 모듈의 단위 테스트.
에러 추출, 중복 제거, 버그 후보 구조체 생성을 검증한다.
"""

import pytest
from Scripts.modules.log_analyzer import (
    extract_error_blocks,
    build_bug_candidates,
    _is_error_line,
    _make_title,
)


class TestIsErrorLine:
    def test_detects_error_keyword(self):
        assert _is_error_line("2024-01-01T00:00:00 ERROR something went wrong")

    def test_detects_critical_keyword(self):
        assert _is_error_line("CRITICAL database connection lost")

    def test_detects_traceback(self):
        assert _is_error_line("Traceback (most recent call last):")

    def test_detects_exception(self):
        assert _is_error_line("  raise Exception('bad value')")

    def test_detects_fatal(self):
        assert _is_error_line("FATAL: out of memory")

    def test_normal_line_not_detected(self):
        assert not _is_error_line("INFO server started on port 8080")

    def test_debug_line_not_detected(self):
        assert not _is_error_line("DEBUG fetching data")


class TestExtractErrorBlocks:
    def test_empty_log_returns_empty(self):
        assert extract_error_blocks("") == []

    def test_no_error_returns_empty(self):
        log = "INFO line1\nINFO line2\nDEBUG line3"
        assert extract_error_blocks(log) == []

    def test_single_error_extracted(self):
        lines = ["INFO before1", "INFO before2", "ERROR bad thing", "INFO after1", "INFO after2"]
        log = "\n".join(lines)
        blocks = extract_error_blocks(log, context_lines=2)
        assert len(blocks) == 1
        assert "ERROR bad thing" in blocks[0]["log_context"]

    def test_context_lines_included(self):
        lines = [f"line{i}" for i in range(20)]
        lines[10] = "ERROR problem"
        log = "\n".join(lines)
        blocks = extract_error_blocks(log, context_lines=3)
        assert len(blocks) == 1
        context = blocks[0]["log_context"]
        # 전후 3줄 포함 확인
        assert "line7" in context
        assert "line13" in context

    def test_duplicate_errors_deduplicated(self):
        # 동일한 에러 메시지가 두 번 등장
        error_block = "INFO ctx\nERROR same error\nINFO ctx2"
        log = error_block + "\n" + error_block
        blocks = extract_error_blocks(log, context_lines=1)
        # 중복 제거로 1개만 반환
        assert len(blocks) == 1

    def test_different_errors_both_extracted(self):
        log = "\n".join([
            "INFO a",
            "ERROR first error",
            "INFO b",
            "INFO c",
            "INFO d",
            "INFO e",
            "INFO f",
            "INFO g",
            "ERROR second error",
            "INFO h",
        ])
        blocks = extract_error_blocks(log, context_lines=1)
        assert len(blocks) == 2

    def test_block_has_required_fields(self):
        log = "INFO before\nERROR test error\nINFO after"
        blocks = extract_error_blocks(log)
        assert len(blocks) == 1
        block = blocks[0]
        assert "error_message" in block
        assert "log_context" in block
        assert "occurred_at" in block

    def test_traceback_extracted(self):
        log = "INFO start\nTraceback (most recent call last):\n  File 'foo.py', line 1\nValueError: bad\nINFO end"
        blocks = extract_error_blocks(log, context_lines=2)
        assert len(blocks) >= 1
        assert any("Traceback" in b["log_context"] for b in blocks)


class TestBuildBugCandidates:
    def test_empty_pod_logs_returns_empty(self):
        assert build_bug_candidates({}) == []

    def test_no_error_logs_returns_empty(self):
        pod_logs = {"pod-1": "INFO all good\nINFO still good"}
        assert build_bug_candidates(pod_logs) == []

    def test_candidate_has_all_fields(self):
        pod_logs = {"my-pod": "INFO before\nERROR something failed\nINFO after"}
        candidates = build_bug_candidates(pod_logs)
        assert len(candidates) == 1
        c = candidates[0]
        assert c["pod_name"] == "my-pod"
        assert "title" in c
        assert "error_message" in c
        assert "log_context" in c
        assert "occurred_at" in c

    def test_multiple_pods_aggregated(self):
        pod_logs = {
            "pod-a": "ERROR error in A",
            "pod-b": "ERROR error in B",
        }
        candidates = build_bug_candidates(pod_logs)
        pod_names = {c["pod_name"] for c in candidates}
        assert "pod-a" in pod_names
        assert "pod-b" in pod_names


class TestMakeTitle:
    def test_short_message_unchanged(self):
        msg = "ERROR something"
        title = _make_title(msg)
        assert title == msg

    def test_long_message_truncated(self):
        msg = "ERROR " + "x" * 100
        title = _make_title(msg, max_len=20)
        assert len(title) <= 23  # max_len + "..."
        assert title.endswith("...")

    def test_whitespace_normalized(self):
        msg = "ERROR   multiple   spaces"
        title = _make_title(msg)
        assert "  " not in title
