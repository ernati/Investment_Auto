"""
log_analyzer.py

수집된 Pod 로그에서 에러 패턴을 필터링하고 버그 후보 구조체를 생성하는 모듈.
"""

import hashlib
import logging
import re
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

# 에러 키워드 패턴 (대소문자 구분)
ERROR_PATTERNS: list[re.Pattern] = [
    re.compile(r"\bERROR\b"),
    re.compile(r"\bCRITICAL\b"),
    re.compile(r"Traceback \(most recent call last\)"),
    re.compile(r"\bException\b"),
    re.compile(r"\bFATAL\b"),
]

# 타임스탬프 파싱 (kubectl --timestamps 형식: 2024-01-01T00:00:00.000000000Z)
_TIMESTAMP_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})")


def extract_error_blocks(
    log_text: str,
    context_lines: int = 5,
) -> list[dict]:
    """로그 텍스트에서 에러 블록을 추출한다.

    에러 키워드를 포함하는 라인과 전후 context_lines 줄을 묶어 에러 블록으로 반환한다.
    동일한 에러 패턴의 중복 블록은 제거된다.

    Args:
        log_text: 분석할 로그 문자열
        context_lines: 에러 라인 전후로 포함할 컨텍스트 줄 수

    Returns:
        에러 블록 문자열 리스트. 에러가 없으면 빈 리스트.
    """
    if not log_text:
        return []

    lines = log_text.splitlines()
    error_line_indices: list[int] = []

    for i, line in enumerate(lines):
        if _is_error_line(line):
            error_line_indices.append(i)

    if not error_line_indices:
        return []

    # 인접한 인덱스들을 묶어 블록 범위 계산
    block_ranges = _merge_ranges(error_line_indices, context_lines, len(lines))

    # 중복 제거를 위한 해시 집합
    seen_hashes: set[str] = set()
    blocks: list[dict] = []

    for start, end, anchor_idx in block_ranges:
        block_lines = lines[start:end]
        block_text = "\n".join(block_lines)
        block_hash = _normalize_hash(block_text)

        if block_hash in seen_hashes:
            logger.debug("중복 에러 블록 제거 (hash=%s)", block_hash[:8])
            continue
        seen_hashes.add(block_hash)

        # 에러 메시지는 anchor 라인 (첫 번째 에러 라인)
        anchor_line = lines[anchor_idx]
        error_message = _strip_timestamp(anchor_line)
        occurred_at = _parse_timestamp(anchor_line)

        blocks.append(
            {
                "error_message": error_message,
                "log_context": block_text,
                "occurred_at": occurred_at,
            }
        )

    return blocks


def build_bug_candidates(
    pod_logs: dict[str, str],
    context_lines: int = 5,
) -> list[dict]:
    """Pod 로그 딕셔너리 전체에서 버그 후보 구조체 목록을 생성한다.

    Args:
        pod_logs: {pod_name: log_text} 딕셔너리
        context_lines: extract_error_blocks에 전달할 컨텍스트 줄 수

    Returns:
        버그 후보 구조체 리스트.
        각 구조체는 {title, error_message, log_context, pod_name, occurred_at} 필드를 갖는다.
        에러가 없으면 빈 리스트를 반환한다.
    """
    candidates: list[dict] = []

    for pod_name, log_text in pod_logs.items():
        blocks = extract_error_blocks(log_text, context_lines=context_lines)
        for block in blocks:
            title = _make_title(block["error_message"])
            candidates.append(
                {
                    "title": title,
                    "error_message": block["error_message"],
                    "log_context": block["log_context"],
                    "pod_name": pod_name,
                    "occurred_at": block["occurred_at"],
                }
            )

    logger.info("총 %d개 버그 후보 생성", len(candidates))
    return candidates


# ---------------------------------------------------------------------------
# 내부 헬퍼 함수
# ---------------------------------------------------------------------------


def _is_error_line(line: str) -> bool:
    """라인이 에러 키워드를 포함하는지 확인한다."""
    return any(pattern.search(line) for pattern in ERROR_PATTERNS)


def _merge_ranges(
    indices: list[int],
    context: int,
    total: int,
) -> list[tuple[int, int, int]]:
    """에러 라인 인덱스 목록을 인접 블록으로 병합하여 (start, end, anchor) 튜플 리스트로 반환한다."""
    ranges: list[tuple[int, int, int]] = []
    if not indices:
        return ranges

    current_start = max(0, indices[0] - context)
    current_end = min(total, indices[0] + context + 1)
    current_anchor = indices[0]

    for idx in indices[1:]:
        block_start = max(0, idx - context)
        if block_start <= current_end:
            # 인접/중첩 → 병합
            current_end = min(total, idx + context + 1)
        else:
            ranges.append((current_start, current_end, current_anchor))
            current_start = block_start
            current_end = min(total, idx + context + 1)
            current_anchor = idx

    ranges.append((current_start, current_end, current_anchor))
    return ranges


def _normalize_hash(text: str) -> str:
    """타임스탬프를 제거한 정규화 텍스트의 SHA-256 해시를 반환한다."""
    normalized = _TIMESTAMP_RE.sub("", text)
    return hashlib.sha256(normalized.encode()).hexdigest()


def _strip_timestamp(line: str) -> str:
    """라인 앞의 타임스탬프를 제거한 순수 메시지를 반환한다."""
    return _TIMESTAMP_RE.sub("", line).strip()


def _parse_timestamp(line: str) -> Optional[str]:
    """라인에서 ISO 8601 타임스탬프를 추출한다. 없으면 현재 UTC 시각을 반환한다."""
    match = _TIMESTAMP_RE.match(line)
    if match:
        return match.group(1)
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def _make_title(error_message: str, max_len: int = 80) -> str:
    """에러 메시지에서 Issue 제목용 요약 문자열을 생성한다."""
    # 불필요한 공백 정리
    summary = " ".join(error_message.split())
    if len(summary) > max_len:
        summary = summary[:max_len].rstrip() + "..."
    return summary
