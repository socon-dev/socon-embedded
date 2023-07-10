import pytest

from pathlib import Path

from socon.core.management import call_command

CURRENT_DIR = Path(__file__).parent.resolve()


class BuildCommandlineTests:

    def test_check_available_subcommands(self, capsys):
        """Check that all subcommands are present"""
        with pytest.raises(SystemExit):
            call_command("build")
        captured = capsys.readouterr()
        assert "fromfile (P)" in captured.out

    def test_build_from_file(self, tmpdir):
        tmp = tmpdir.mkdir("artifact")
        call_command(
            "build", "fromfile", "--file",
            f"{CURRENT_DIR}/app_configs/simple_app_config.yml",
            "--project", "tests", "--artifact-dir", tmp
        )
