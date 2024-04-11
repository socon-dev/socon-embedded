from socon_embedded.schema.task import Task

from socon_embedded.executor.task_executor import TaskExecutor


class BaseTestTask:

    def run_with_task_executor(self, task: Task) -> dict:
        executor = TaskExecutor(task)
        return executor.run()
