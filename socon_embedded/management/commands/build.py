from argparse import ArgumentParser
from collections.abc import MutableMapping
import os
from typing import Any, Dict, Optional, Tuple

from socon_embedded.utils.loader import from_json_or_yaml, load_from_file
from socon_embedded.utils.converter import to_text
from socon_embedded.utils.parser import parse_key_value

from socon.core.management.base import CommandError, Config, ProjectCommand
from socon.core.management.subcommand import Subcommand
from socon.core.registry.config import ProjectConfig


class BuildCommand(Subcommand):
    help = "Build a project application"
    subcommand_manager = "build_manager"


class BuildCommandInterface(ProjectCommand, abstract=True):
    manager = "build_manager"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--app", help="The name of the application to build", action="append"
        )
        parser.add_argument(
            "--group",
            help="The group name of the applications to build",
            action="append",
        )
        parser.add_argument("--mode", help="The building mode", action="append")
        parser.add_argument(
            "--builder", help="The name of the builder", action="append"
        )
        parser.add_argument(
            "--base-dir",
            help=("Base build directory for the application that needs to be build"),
        )
        parser.add_argument(
            "--filter",
            help=(
                "Set filter to build only specific application. "
                'Example: --filter "name=myapp", --filter "group__in=[\'xx\']"'
            ),
            action="append",
        )
        parser.add_argument(
            "--exclude",
            help=(
                "Set filter to exclude specific application from being built. "
                'Example: --exclude "name=myapp", --exclude "group__in=[\'xx\']"'
            ),
            action="append",
        )
        parser.add_argument(
            "--extras-vars",
            help=(
                "Set variables as key=value or YAML/JSON, if filename prepend with @. "
                'Example: --set-vars "fruit=apple", --set-vars "@file.yml"'
            ),
            action="append",
        )
        parser.add_argument(
            "--eoe",
            "--exit-on-error",
            help="Exit if there is an error",
            action="store_true",
        )
        parser.add_argument(
            "--wae", "--warning-as-error", help="Treat a warning as an error"
        )
        parser.add_argument(
            "--artifact-dir", help=(
                "Path to the artifact folder that will store "
                "the build artifacts"
            )
        )
        self.add_build_arguments(parser)

    def add_build_arguments(self, parser: ArgumentParser) -> None:
        """Add more arguments to the base build arguments"""
        pass

    def handle(self, config: Config, project_config: ProjectConfig) -> str:
        # Transform each of the following command line args as a dictionary
        filters = self.load_template_args(config.getoption("filter", []))
        excludes = self.load_template_args(config.getoption("excludes", []))
        extras_vars = self.load_template_args(config.getoption("extras_vars", []))

        # Merge the extras filters with the default one passed on the command line
        filters_opt = self._create_filter(
            ("name__in", config.getoption("name")),
            ("group__in", config.getoption("group")),
            ("builders__name__in", config.getoption("builder")),
            ("builders__mode__in", config.getoption("mode")),
        )
        filters = filters | filters_opt

        # Create a context based on the extras vars and the base directory. This
        # will be mainly use to resolve any further jinja template file
        base_dir = config.getoption("base_dir")
        context = extras_vars
        if base_dir is not None:
            context.update({"base_dir": base_dir})

        # Get exit condition and pass them to the handle_build method.
        eoe = config.getoption("eoe")
        wae = config.getoption("wae")

        # Get the output directory if any
        artifact_dir = config.getoption("artifact_dir")

        # Load every variable that needs to be export in the project config
        env_variables = project_config.get_setting(
            "BUILD_ENVIRONMENT_VARIABLE", skip=True, default=[]
        )
        for env, value in env_variables:
            if os.environ.get(env) is not None:
                os.environ[env] += os.pathsep + value
            else:
                os.environ[env] = value

        # Pass all the above to a method used by each subcommands
        self.handle_build(
            config=config,
            project_config=project_config,
            filters=filters,
            excludes=excludes,
            exit_on_error=eoe,
            context=context,
            warning_as_error=wae,
            artifact_dir=artifact_dir
        )

    def handle_build(
        self,
        config: Config,
        project_config: ProjectConfig,
        filters: dict = {},
        excludes: dict = {},
        context: dict = {},
        exit_on_error: bool = False,
        warning_as_error: bool = False,
        artifact_dir: str = None
    ) -> str:
        raise NotImplementedError(
            "Subclass of '{}' must implement handle_build(...) method".format(
                self.__class__.__name__
            )
        )

    @staticmethod
    def load_template_args(vars: list[Any] = tuple()) -> Dict[str, str]:
        """Load vars passed in command line arguments"""
        loaded_vars = {}

        for var_opt in vars:
            data = None
            var_opt = to_text(var_opt)
            if var_opt is None or not var_opt:
                continue
            if var_opt.startswith("@"):
                # Argument is a YAML file (JSON is a subset of YAML)
                data = load_from_file(var_opt[1:])
            elif var_opt[0] in ["/", "."]:
                raise CommandError(
                    f"Please prepend set-vars filename '{var_opt}' with '@'"
                )
            elif var_opt[0] in ["[", "{"]:
                # Arguments as YAML
                data = from_json_or_yaml(var_opt)
            else:
                # Arguments as Key-value
                data = parse_key_value(var_opt)

            if isinstance(data, MutableMapping):
                loaded_vars = loaded_vars | data
            else:
                raise CommandError(
                    f"Invalid extra vars data supplied. '{var_opt}' could "
                    "not be made into a dictionary"
                )

        return loaded_vars

    @staticmethod
    def _create_filter(*filters: Tuple[str, Optional[dict]]) -> dict:
        output = {}
        for key, value in filters:
            if value is not None:
                output[key] = value
        return output
