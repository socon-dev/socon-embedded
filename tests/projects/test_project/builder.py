from socon_embedded.builder import Builder


class EchoBuilder(Builder):
    name = "echo"
    use_shell = True

    def get_executable(self) -> str:
        return "echo"

    def get_main_args(self, project_file, **variant_args) -> list[str]:
        return [project_file]
