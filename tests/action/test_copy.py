from pathlib import Path

from socon_embedded.schema.task import Task
from tests.action import BaseTestTask


class TestCopyTask(BaseTestTask):

    def test_copy_file_to_a_folder(self, tmpdir):
        temp_d_1 = tmpdir.mkdir("sub_1").join("hello.txt")
        temp_d_1.write("content")
        temp_d_2 = tmpdir.mkdir("sub_2")
        task = Task(
            **{
                "name": "Copy file to a folder",
                "copy": {"src": str(temp_d_1), "dest": str(temp_d_2)},
            }
        )
        result = self.run_with_task_executor(task)
        assert result["failed"] is False
        assert Path(temp_d_2, "hello.txt").exists() == True

    def test_copy_folder_to_a_new_folder(self, tmpdir):
        temp_d_1 = tmpdir.mkdir("sub_1").join("content.txt")
        temp_d_1.write("content")
        destination = Path(tmpdir, "sub_2")
        task = Task(
            **{
                "name": "Copy folder to a folder",
                "copy": {"src": str(Path(tmpdir, "sub_1")), "dest": str(destination)},
            }
        )
        result = self.run_with_task_executor(task)
        assert result["failed"] is False
        assert Path(destination).exists() == True
        assert Path(destination, "content.txt").exists() == True

    def test_copy_content_to_a_file(self, tmpdir):
        temp_d_1 = tmpdir.mkdir("sub_1").join("hello.txt")
        task = Task(
            **{
                "name": "Copy content to a file",
                "copy": {"content": "Simple content", "dest": str(temp_d_1)},
            }
        )
        result = self.run_with_task_executor(task)
        assert result["failed"] is False
        assert temp_d_1.read() == "Simple content"
