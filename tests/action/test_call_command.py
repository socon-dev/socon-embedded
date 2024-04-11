from pathlib import Path

from socon_embedded.schema.task import Task

from tests.action import BaseTestTask


class TestCallCommandTask(BaseTestTask):

    def test_run_createcontainer_command(self, tmpdir):
        container = Path(tmpdir, "task_container")
        task = Task(
            **{
                "name": "Run simple command",
                "call_command": {
                    "cmd": "createcontainer",
                    "argv": ["task_container", "--target", str(container)],
                },
            }
        )
        result = self.run_with_task_executor(task)
        assert result["failed"] is False
        assert Path(tmpdir, "task_container").exists() is True
