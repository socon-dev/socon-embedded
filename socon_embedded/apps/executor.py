import os
from pathlib import Path
import shutil

from typing import Any, Dict, List, Union

from socon_embedded.builder.result import BuildResult, Result, Status
from socon_embedded.managers import BuilderManager
from socon_embedded.schema.apps import AppRegistry
from socon_embedded.builder import BuildInfo, Builder
from socon_embedded.schema.tasks.executor import Executor, TaskExecutor
from socon_embedded.schema.tasks.task import Task

from socon.core.registry import projects
from socon.core.registry.config import ProjectConfig
from socon.utils.terminal import terminal
from socon.conf import settings

from junitparser import JUnitXml, TestCase, TestSuite, Failure, Skipped


def execute_tasks(tasks: List[Task]) -> None:
    """
    Execute a task. Exit on any exception and clean the task.
    """
    for task in tasks:
        tsx = TaskExecutor(task)
        tsx.run()


class AppRegistryExecutor(Executor):

    def __init__(
        self,
        app_registry: AppRegistry,
        builder_manager: BuilderManager,
        project_config: ProjectConfig = None
    ) -> None:
        self._app_registry = app_registry
        self._builder_manager = builder_manager
        self._project_config = project_config

        # Load the project config if none are given
        if self._project_config is None:
            try:
                self._project_config = projects.get_project_config_by_env()
            except LookupError:
                pass

        # Cache for used builder when building the application in the registry
        self._cached_builders: Dict[str, Builder] = {}

        # Cache for applications results
        self._build_results: list[BuildResult] = []

    def _clear_cache(self):
        self._cached_builders = {}
        self._build_results = []

    @classmethod
    def from_file(cls, file: Union[str, os.PathLike], context: dict = {}, **kwargs):
        """Create an AppRegistry from a yaml/json file"""
        app_registry = AppRegistry.load(file, context)
        return cls(app_registry, **kwargs)

    def build(
        self,
        filters: Dict[str, Any] = {},
        excludes: Dict[str, Any] = {},
        output_dir: Union[str, os.PathLike] = None,
        exit_on_error: bool = False,
        warning_as_error: bool = False,
    ):
        """Build the application in each registries based on the given filters"""
        self._clear_cache()

        # Create a build section
        terminal.sep("-", f"Application registry: {self._app_registry.name}", newline="before")

        # Filter the application and return a AppRegistry with only the application
        # that we want to build
        reg = self._app_registry.filter(filters, excludes)

        # Raise a LookupError if we don't find any build configuration
        if not reg.apps:
            raise LookupError(
                "Nothing to build. You should check if you have registered your\n"
                "applications or if your filters are correct."
            )

        # Stop building in case exit_on_error is True and an issue was found.
        # This flag allow to still create a report with the rest of the application
        # set as skipped
        stop_building = False

        # Build each build configuration
        for app_config in reg.apps:

            # Get all build configuration for each application
            build_configs = app_config.get_build_configs()

            for build_config in build_configs:

                # Create a build info object
                build_info = build_config.create_buildinfo()

                # If stop building is True, we still create result with skipped
                # status and the build info
                if stop_building is True:
                    result = BuildResult(
                        Result(Status.SKIPPED, "Skipped due to previous error")
                    )
                    result.build_info = build_info
                    self._build_results.append(result)
                    continue

                # Create the artifact directory
                artifact_path = self._create_artifact_directory(build_info, output_dir)

                # Build the application
                builder = self._get_builder(build_config.builder.name)
                result = builder.build(
                    **build_config.get_buildinfo(),
                    output_file=Path(artifact_path, f"{build_info.app}.log"),
                    warning_as_error=warning_as_error,
                    vars=self._app_registry.vars
                )

                # Save the fail result of the current apps
                self._build_results.append(result)

                # In case we need to exit on error. We need to stop the build
                # of all application but still put the next application that
                # were not build as skipped for the junit report.
                if result.is_fail and exit_on_error is True:
                    stop_building = True

    def _create_artifact_directory(
        self,
        build_info: BuildInfo,
        output_dir: str = None,
        clean: bool = False
    ):
        """
        Save the output in an artifact directory at the current location or
        inside the specified output directory.
        If clean = True, the directory will be cleaned
        """
        output_dir = output_dir if output_dir else os.getcwd()
        artifact_path = list(filter(None, [
            output_dir, self._app_registry.name, build_info.builder, build_info.app,
            "_".join(sorted(build_info.variant_args.values()))
        ]))
        artifact_path = Path().joinpath(*artifact_path)

        # In case the result folder does not exist, we create it. In case the
        # clean options is set, we remove and recreate the folder.
        if artifact_path.is_dir():
            if clean:
                shutil.rmtree(artifact_path)
                os.mkdir(artifact_path)
        else:
            os.makedirs(artifact_path, exist_ok=True)

        return artifact_path

    def create_report(
        self,
        output_file: str,
        output_dir: str = None,
        add_skipped_apps: bool = True
    ) -> None:
        """Create junit report from buidled and skipped apps"""
        output_dir = output_dir if output_dir else getattr(
            settings, "ARTIFACT_PATH", default=os.getcwd())
        junit_file = Path(output_dir) / output_file

        # Create the Junit object
        junit = JUnitXml()

        # If there is no builded application, we return an empty junitxml file
        if not self._build_results:
            junit.write(str(junit_file), pretty=True)
            return

        # Iterate over all build results
        testsuite = TestSuite(self._app_registry.name)
        for result in self._build_results:
            testcase = TestCase(result.build_info.get_case_name())
            testcase.time = result.execution_time

            # Assign a Failure or Skipped result to the testcase
            if result.is_fail:
                testcase.result = Failure(result.result.text)
            elif result.is_skipped:
                testcase.result = Skipped(result.result.text)

            # Do not add testcase that are skipped if add_skipped_apps is False
            if result.is_skipped and add_skipped_apps is False:
                continue

            testsuite.add_testcase(testcase)

        # Create the report
        junit.write(str(junit_file), pretty=True)

        # Return the junit report in case someone needs to use it
        return junit

    def _get_builder(self, name: str) -> Builder:
        """Get the builder in cache or via the manager"""
        if name in self._cached_builders:
            builder = self._cached_builders.get(name)
        else:
            builder_klass = self._builder_manager.search_hook_impl(name, self._project_config)
            builder = builder_klass()
            self._cached_builders[name] = builder

        return builder
