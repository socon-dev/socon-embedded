from socon.core.management import call_command


class TestFromFileCommand:
    def test_build_from_file(self, tmpdir, datafix_dir):
        tmp = tmpdir.mkdir("artifact")
        call_command(
            "build",
            "fromfile",
            "--file",
            f"{datafix_dir}/simple_app_config.yml",
            "--project",
            "test_project",
            "--artifact-dir",
            tmp,
        )
