from argparse import ArgumentParser
from pathlib import Path

from socon_embedded.apps.executor import AppRegistryExecutor
from socon_embedded.management.commands.build import BuildCommandInterface

from socon.core.management.base import Config
from socon.core.registry.config import ProjectConfig

from socon_embedded.managers import get_builder_manager


class BuildFromFile(BuildCommandInterface):
    name = "fromfile"

    def add_build_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--file",
            help="Path to the YML application configuration file",
            required=True,
            type=Path,
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
        artifact_dir: str = None,
    ) -> str:
        # Get all the registries that the user want to run
        app_registry = config.getoption("file")

        # Create the RegistryExecutor that will handle the execution of
        # all registries
        regexec = AppRegistryExecutor.from_file(
            app_registry,
            context=context,
            project_config=project_config,
            builder_manager=get_builder_manager()
        )

        # Build the application using the selected registry
        regexec.build(
            filters=filters,
            excludes=excludes,
            exit_on_error=exit_on_error,
            warning_as_error=warning_as_error,
            output_dir=artifact_dir
        )
