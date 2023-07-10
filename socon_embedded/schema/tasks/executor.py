from abc import ABC

from socon_embedded.schema.tasks.task import Task


class Executor(ABC):
    pass


class TaskPlayer(Executor):

    def __init__(self) -> None:
        self._played_tasks: list[TaskExecutor] = []

    def run(self, tasks: list[Task]) -> None:
        for task in tasks:
            taskexc = TaskExecutor(task)
            taskexc.run()

    def cleanup(self) -> None:
        """Clean all previous tasks execution if they have define a cleanup method"""
        for task in self._played_tasks:
            task.cleanup()


class TaskExecutor(Executor):

    def __init__(self, task: Task) -> None:
        self._task = task

    def run(self) -> None:
        print(f"TASK: {self._task.name}")

    def cleanup(self):
        print(f"TASK cleanup: {self._task.name}")
