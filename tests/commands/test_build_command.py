import pytest

from socon.core.management import call_command


class TestBuildCommand:

    def test_check_available_subcommands(self, capsys):
        """Check that all subcommands are present"""
        with pytest.raises(SystemExit):
            call_command("build")
        captured = capsys.readouterr()
        assert "fromfile (P)" in captured.out
