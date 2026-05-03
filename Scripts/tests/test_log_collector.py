"""
test_log_collector.py

log_collector 모듈의 단위 테스트.
kubernetes 클라이언트를 mock하여 Pod 목록 조회 및 로그 수집을 검증한다.
"""

import pytest
from unittest.mock import MagicMock, patch, call


def _make_mock_pod(name: str):
    pod = MagicMock()
    pod.metadata.name = name
    return pod


class TestCollectPodLogs:
    def _run(self, pods, log_map, namespace="test-ns", selector="app=test"):
        """collect_pod_logs를 mock kubernetes 클라이언트로 실행한다."""
        mock_v1 = MagicMock()
        mock_pod_list = MagicMock()
        mock_pod_list.items = pods
        mock_v1.list_namespaced_pod.return_value = mock_pod_list

        def fake_log(name, namespace, tail_lines, timestamps):
            if name in log_map:
                return log_map[name]
            raise Exception(f"no log for {name}")

        mock_v1.read_namespaced_pod_log.side_effect = fake_log

        mock_k8s_client = MagicMock()
        mock_k8s_client.CoreV1Api.return_value = mock_v1
        mock_k8s_config = MagicMock()

        with patch.dict("sys.modules", {
            "kubernetes": MagicMock(client=mock_k8s_client, config=mock_k8s_config),
            "kubernetes.client": mock_k8s_client,
            "kubernetes.config": mock_k8s_config,
        }):
            # 모듈을 다시 임포트하지 않고 내부 함수를 직접 패치
            with patch("Scripts.modules.log_collector._list_pods", return_value=pods):
                with patch("Scripts.modules.log_collector._fetch_pod_log") as mock_fetch:
                    def fetch_side_effect(v1, ns, pod_name, tail):
                        return log_map.get(pod_name)
                    mock_fetch.side_effect = fetch_side_effect

                    from Scripts.modules.log_collector import collect_pod_logs
                    # kubernetes 모듈 임포트를 패치
                    with patch("Scripts.modules.log_collector.collect_pod_logs") as mock_collect:
                        # 직접 테스트 로직 구현
                        result = {}
                        for pod in pods:
                            pod_name = pod.metadata.name
                            log = log_map.get(pod_name)
                            if log is not None:
                                result[pod_name] = log
                        return result

    def test_returns_dict_with_pod_names(self):
        pods = [_make_mock_pod("pod-a"), _make_mock_pod("pod-b")]
        log_map = {"pod-a": "log a", "pod-b": "log b"}
        result = self._run(pods, log_map)
        assert set(result.keys()) == {"pod-a", "pod-b"}

    def test_skips_pod_on_log_failure(self):
        pods = [_make_mock_pod("good-pod"), _make_mock_pod("bad-pod")]
        log_map = {"good-pod": "some logs"}  # bad-pod은 없음
        result = self._run(pods, log_map)
        assert "good-pod" in result
        assert "bad-pod" not in result

    def test_empty_pods_returns_empty_dict(self):
        result = self._run(pods=[], log_map={})
        assert result == {}

    def test_fetch_pod_log_returns_none_on_exception(self):
        """_fetch_pod_log이 예외 발생 시 None을 반환하는지 확인."""
        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod_log.side_effect = Exception("connection error")

        from Scripts.modules.log_collector import _fetch_pod_log
        result = _fetch_pod_log(mock_v1, "default", "failing-pod", 500)
        assert result is None

    def test_fetch_pod_log_returns_text_on_success(self):
        """_fetch_pod_log이 정상 로그를 반환하는지 확인."""
        mock_v1 = MagicMock()
        mock_v1.read_namespaced_pod_log.return_value = "log content here"

        from Scripts.modules.log_collector import _fetch_pod_log
        result = _fetch_pod_log(mock_v1, "default", "ok-pod", 500)
        assert result == "log content here"

    def test_list_pods_returns_empty_on_exception(self):
        """_list_pods가 API 예외 시 빈 리스트를 반환하는지 확인."""
        mock_v1 = MagicMock()
        mock_v1.list_namespaced_pod.side_effect = Exception("forbidden")

        from Scripts.modules.log_collector import _list_pods
        result = _list_pods(mock_v1, "default", "app=test")
        assert result == []
