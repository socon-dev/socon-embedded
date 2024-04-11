from unittest.mock import MagicMock

from socon_embedded.executor.task_result import TaskResult


class TestTaskResult:
    def test_task_result_basic(self):
        mock_task = MagicMock()
        _ = TaskResult(mock_task, dict())

    def test_task_result_is_failed(self):
        mock_task = MagicMock()

        # test with no failed in result
        tr = TaskResult(mock_task, dict())
        assert tr.is_failed() is False

        # test with failed in result
        tr = TaskResult(mock_task, dict(failed=True))
        assert tr.is_failed() is True
