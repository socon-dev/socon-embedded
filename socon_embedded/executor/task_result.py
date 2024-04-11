from socon_embedded.schema.task import Task


class TaskResult:
    """
    This class is responsible for interpreting the resulting data
    from an executed task, and provides helper methods for determining
    the result of a given task.
    """

    def __init__(self, task: Task, return_data: dict):
        self._task = task
        self._result = return_data

    @property
    def task_name(self):
        return self._task.name

    def is_changed(self):
        return self._check_key("changed")

    def is_skipped(self):
        return self._result.get("skipped", False)

    def is_failed(self):
        return self._check_key("failed")

    def _check_key(self, key):
        """get a specific key from the result or its items"""
        return self._result.get(key, False)
