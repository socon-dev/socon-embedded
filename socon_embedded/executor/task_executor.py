import json
import traceback

from typing import Optional
from collections import OrderedDict

from socon_embedded.executor.task_result import TaskResult
from socon_embedded.schema.task import Task
from socon_embedded.utils.converter import to_text

from socon.utils.terminal import terminal


class TaskTimeoutError(BaseException):
    pass


def task_timeout(signum, frame):
    raise TaskTimeoutError


class TaskPlayer:

    def __init__(self) -> None:
        self._played_tasks: list[TaskExecutor] = []
        self._terminal = terminal

    def run(self, tasks: list[Task]) -> None:
        for task in tasks:
            executor = TaskExecutor(task, {})
            self._task_on_start(task)
            result = executor.run()
            tr = TaskResult(task, result)
            if tr.is_failed():
                self._task_on_failed(tr)
                executor.cleanup()
                for played_exec in self._played_tasks:
                    played_exec.cleanup()
                return
            self._task_on_ok(tr)
            self._played_tasks.append(executor)
        if len(self._played_tasks) != 0:
            self._terminal.line()

    def cleanup(self) -> None:
        for executor in self._played_tasks:
            executor.cleanup()

    def _task_on_start(self, task: Task):
        if self._terminal._current_line not in ["", "\n", "\r"]:
            self._terminal.line()
        self._terminal.line(f"TASK [{task.name}]")
        self._terminal.sep("*")

    def _task_on_failed(self, result: TaskResult):
        msg = "failed: => {}".format(self._dump_results(result._result))
        self._terminal.line(msg, fg="red")

    def _task_on_ok(self, result: TaskResult):
        self._terminal.line("succesfull")

    def _dump_results(
        self,
        result: dict,
        indent: Optional[int] = 4,
        sort_keys: bool = False,
    ) -> str:
        try:
            return json.dumps(
                result, indent=indent, ensure_ascii=False, sort_keys=sort_keys
            )
        except TypeError:
            return json.dumps(
                OrderedDict(sorted(result.items(), key=to_text)),
                indent=indent,
                ensure_ascii=False,
                sort_keys=False,
            )


class TaskExecutor:

    def __init__(self, task: Task, job_vars: dict = {}) -> None:
        self._task = task
        self._job_vars = job_vars
        self._terminal = terminal

    def run(self) -> dict:
        try:
            res = self._execute()
            return res
        except Exception as e:
            return dict(
                failed=True,
                msg=f"Unexpected failure during module execution: {e}",
                exception=to_text(traceback.format_exc()),
                stdout="",
            )

    def _execute(self, variables: Optional[dict] = None) -> dict:
        if variables is None:
            variables = self._job_vars
            vars_copy = variables.copy()

        retries = 1  # includes the default actual run + retries set by user/default
        if self._task.retries is not None:
            retries += max(0, self._task.retries)

        result = {}
        for attempt in range(1, retries + 1):
            try:
                result = self._task.action.run(tasks_vars=vars_copy)
            except Exception as e:
                self._task.action.cleanup()
                raise e

            # set the failed property if it was missing.
            if "failed" not in result:
                result["failed"] = False

            # Make attempts and retries available early to allow their use in changed/failed_when
            if retries > 1:
                result["attempts"] = attempt
        else:
            if retries > 1:
                # we ran out of attempts, so mark the result as failed
                result["attempts"] = retries - 1
                result["failed"] = True

        return result

    def cleanup(self):
        self._task.action.cleanup()

    def _task_on_retry(self, result: dict):
        msg = "FAILED - RETRYING:  ({} retries left).".format(
            self._task.name, result["retries"] - result["attempts"]
        )
        self._terminal.line(msg)
