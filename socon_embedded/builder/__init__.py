from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
import sys
import time

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence, Tuple, Union

from socon_embedded.builder.parser import DefaultParser
from socon_embedded.builder.result import Result, Status
from socon_embedded.utils.converter import safe_decode
from socon_embedded.builder.result import BuildResult

from socon.core.manager import Hook
from socon.utils.terminal import terminal


logger = logging.getLogger(__name__)


class BuildCommandNotFound(Exception):
    def __init__(self, command: list[str], cause: Exception) -> None:
        self.command = command
        cause = "{}('{}')".format(type(cause).__name__, safe_decode(str(cause)))
        self._cmd = safe_decode(self.command[0])
        self._cmdline = " ".join(safe_decode(i) for i in self.command)
        self._cause = cause and f" due to: {cause}" or "!"

    def __str__(self) -> str:
        return ("Cmd('{}') not found{}" + "\n  cmdline: {}").format(
            self._cmd, self._cause, self._cmdline
        )


@dataclass
class BuildInfo:
    """Store building information"""
    app: str
    builder: str
    project_file: str
    variant_args: dict = field(default_factory=dict)
    cmdline: list = field(default_factory=list)

    def __str__(self) -> str:
        output = [
            f"Application: {self.app}",
            f"Input file: {self.project_file}",
            f"Builder: {self.builder}"
        ]
        variant_args = self.variant_args
        if variant_args:
            for key, value in variant_args.items():
                output.append(f"{key.title()}: {value}")
        return "\n".join(output)

    def get_case_name(self) -> str:
        """Get the testcase name that will be used in the junit report"""
        return " - ".join([
            self.app,
            self.builder,
            *self.variant_args.values()
        ])


class Builder(Hook, abstract=True):
    """Base class for toolchain or compiler"""

    manager = "builder"

    # Default options defined by the user
    persistant_options: list[str] = []

    # If True, a shell will be used when executing git commands.
    use_shell = False

    def __init__(
        self,
        name: Optional[str] = None,
        executable: Optional[Union[str, os.PathLike]] = None
    ) -> None:
        self.name = name or getattr(self, "name", self.__class__.__name__)
        self.executable = executable or self.get_executable()
        if not self.executable:
            raise AttributeError(
                "'executable' attribute is required by '{}'".format(self.name)
            )

        # User can define the parser as a class attribute if needed
        if not hasattr(self, "parser"):
            self.parser = DefaultParser

    def get_executable(self) -> str:
        """Get the builder executable"""
        return getattr(self, "executable")

    def build(
        self,
        app: str,
        project_file: Union[str, os.PathLike],
        variant_args: dict = {},
        raw_args: list[str] = [],
        warning_as_error: bool = False,
        output_file: Union[str, os.PathLike] = None,
        clean: bool = False,
        vars: dict = {},
        **kwargs: Any,
    ) -> BuildResult:
        """
        Compile an application using the input path, the specified mode and arguments
        """
        main_args = self.get_main_args(project_file, **variant_args)
        if isinstance(main_args, str):
            main_args = main_args.split()

        # Raise an error if main_args is None
        if main_args is None:
            raise RuntimeError(
                "'get_main_args' method must return a list or a string of args"
            )

        # Add the user options
        args_list = main_args + raw_args

        # Build the command line arguments
        cmdline = [self.executable]
        cmdline.extend(args_list)

        # Add persistent builder options
        cmdline.extend(self.persistant_options)

        # if warning_as_error is True, we check if the builder has registered
        # a command line option for that purpose. If it's the case, we check that
        # this option was not already define
        if warning_as_error is True:
            wae_args = self.get_warning_as_error_arg()
            if isinstance(wae_args, str):
                wae_args = wae_args.split()
            if not all(wae_arg in cmdline for wae_arg in wae_args):
                cmdline.extend(wae_args)

        # Create the build info object
        buildinfo = BuildInfo(
            app=app,
            builder=self.name,
            project_file=project_file,
            cmdline=cmdline,
            variant_args=variant_args
        )
        self.display_build_info(buildinfo)

        # Run pre_build method if required
        self.pre_build(buildinfo, **vars)

        # Get an approximation build time execution
        time_started = time.time()

        # Build the application. In case the command is not found, we catch
        # the exception and make a result out of it.
        try:
            status_code, output = self.execute(cmdline, **kwargs)
        except BuildCommandNotFound as e:
            build_result = BuildResult(
                Result(Status.FAILURE, str(e)), str(e)
            )
        else:
            # Get the execution time of the build
            execution_time = time.time() - time_started

            # Load the parser, parse and interpret the results
            parser = self.parser(warning_as_error)
            build_result = parser.execute(status_code, output)
            build_result.execution_time = execution_time

        # Save the build info for later use
        build_result.build_info = buildinfo

        # Display the result. Let the user re-define that if wanted
        self.display_result(build_result)

        # Save the log into the artifact path
        if output_file:
            with open(output_file, 'w+') as f:
                f.write(build_result.output)

        # call the post_build method
        output_dir = Path(output_file).parent
        self.post_build(build_result, output_dir, **vars)

        return build_result

    @abstractmethod
    def get_main_args(
        self, project_file: Union[str, os.PathLike], **variant_args
    ) -> list[str]:
        """Return the main command line argument for the builder"""
        pass

    def execute(
        self, commands: list[str],
        **subprocess_args: Any
    ) -> Tuple[int, Union[str, bytes], str]:
        return self._execute(commands, **subprocess_args)

    def display_result(self, build_result: BuildResult) -> None:
        """Display build result"""
        status_msg = build_result.get_status_message()
        color = "green"
        if build_result.is_fail:
            color = "red"
        if build_result.result.message:
            terminal.line(build_result.result.message)
        terminal.line(f"Result: {status_msg}\n", fg=color)

    def pre_build(self, build_info: BuildInfo, **vars):
        """Method executed just before the build execution"""
        pass

    def post_build(self, result: BuildResult, **vars):
        """Method executed after the build execution"""
        pass

    def display_build_info(self, buildinfo: BuildInfo) -> None:
        terminal.line(str(buildinfo))

    def _execute(
        self,
        command: Sequence[Any],
        silent: bool = True,
        shell: Union[None, bool] = None,
        env: Union[None, Mapping[str, str]] = None,
        **subprocess_kwargs: Any,
    ) -> Tuple[int, Union[str, bytes], str]:
        """
        Handles executing the command on the shell and consumes and returns
        the returned information (status_code, stdout/stderr)
        """

        # Output of the command. Represented as a list to append evert
        # line we read from the subprocess. This allow real-time output
        output = []

        # Don't automatically merge with os.environ for security reasons.
        # Make this forwarding explicit rather than implicit.
        inline_env = env
        env = os.environ.copy()
        if inline_env is not None:
            env.update(inline_env)

        cmd_not_found_exception = FileNotFoundError
        if os.name == "nt":
            cmd_not_found_exception = OSError

        # Make sure the command is a list if shell is False and the command
        # argument given is a string. Otherwise we will have a command error
        if isinstance(command, str):
            command = command.split(" ")

        logger.debug("Running following commands: {}\n".format(command))

        try:
            process = subprocess.Popen(
                command,
                shell=shell is not None and shell or self.use_shell,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                **subprocess_kwargs
            )

            if silent is True:
                print("Building...")

            # Display realtime output and save it
            logger.debug("Command generated following output: ")
            while True:
                stdout = process.stdout.readline()
                return_code = process.poll()
                if not stdout and return_code is not None:
                    break
                if stdout:
                    stdout = safe_decode(stdout)
                    if silent is False:
                        sys.stdout.write(stdout)
                        sys.stdout.flush()
                    output.append(stdout)

        except cmd_not_found_exception as err:
            raise BuildCommandNotFound(command, err) from err
        else:
            output = "".join(output)
            return process.returncode, output

    def get_warning_as_error_arg(self) -> Union[str, list]:
        """Return the command line argument that enable warning as error"""
        return []
