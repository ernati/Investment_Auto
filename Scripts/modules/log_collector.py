"""
log_collector.py

k3s 클러스터의 서비스 Pod 로그를 수집하는 모듈.
kubernetes Python 클라이언트를 사용하여 지정된 namespace/label selector에
해당하는 Pod 목록을 조회하고 각 Pod의 최근 로그를 수집한다.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def collect_pod_logs(
    namespace: str,
    label_selector: str,
    tail_lines: int = 500,
) -> dict[str, str]:
    """지정된 namespace/label_selector에 해당하는 Pod 로그를 수집한다.

    Args:
        namespace: 대상 Kubernetes namespace
        label_selector: Pod를 선택하는 label selector 문자열 (예: "app=my-service")
        tail_lines: 각 Pod에서 가져올 최근 로그 라인 수

    Returns:
        {pod_name: log_text} 형태의 딕셔너리.
        로그 수집에 실패한 Pod는 결과에서 제외된다.
    """
    try:
        from kubernetes import client, config as k8s_config
    except ImportError as exc:
        raise ImportError(
            "kubernetes 패키지가 설치되어 있지 않습니다. "
            "'pip install kubernetes'를 실행하세요."
        ) from exc

    # 클러스터 내부 실행 시 in-cluster config 사용, 로컬 개발 시 kubeconfig 사용
    try:
        k8s_config.load_incluster_config()
    except k8s_config.ConfigException:
        logger.debug("in-cluster config 로드 실패, kubeconfig 사용 시도")
        k8s_config.load_kube_config()

    v1 = client.CoreV1Api()

    # 대상 Pod 목록 조회
    pod_list = _list_pods(v1, namespace, label_selector)
    if not pod_list:
        logger.warning(
            "namespace=%s, label_selector=%s 에 해당하는 Pod가 없습니다.",
            namespace,
            label_selector,
        )
        return {}

    results: dict[str, str] = {}
    for pod in pod_list:
        pod_name: str = pod.metadata.name
        log_text = _fetch_pod_log(v1, namespace, pod_name, tail_lines)
        if log_text is not None:
            results[pod_name] = log_text

    logger.info(
        "총 %d개 Pod 중 %d개 로그 수집 완료 (namespace=%s)",
        len(pod_list),
        len(results),
        namespace,
    )
    return results


def _list_pods(v1, namespace: str, label_selector: str):
    """namespace와 label_selector에 해당하는 Pod 목록을 반환한다."""
    try:
        pod_list = v1.list_namespaced_pod(
            namespace=namespace,
            label_selector=label_selector,
        )
        return pod_list.items
    except Exception as exc:
        logger.error("Pod 목록 조회 실패 (namespace=%s): %s", namespace, exc)
        return []


def _fetch_pod_log(
    v1,
    namespace: str,
    pod_name: str,
    tail_lines: int,
) -> Optional[str]:
    """단일 Pod의 로그를 조회한다. 실패 시 None을 반환하고 로그에 기록한다."""
    try:
        log_text: str = v1.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            tail_lines=tail_lines,
            timestamps=True,
        )
        logger.debug("Pod 로그 수집 완료: %s (%d bytes)", pod_name, len(log_text))
        return log_text
    except Exception as exc:
        logger.warning("Pod 로그 수집 실패 (pod=%s): %s — 건너뜀", pod_name, exc)
        return None
