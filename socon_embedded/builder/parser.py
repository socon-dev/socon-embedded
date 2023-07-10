from abc import ABC, abstractmethod

from socon_embedded.builder.result import BuildResult, Result, Status


class Parser(ABC):
    """Base class for all builder parsers"""

    def __init__(self, warning_as_error: False) -> None:
        self.warning_as_error = warning_as_error

    def execute(self, builder_status: int, output: str) -> BuildResult:
        """Parse and interpret the build result"""
        result = self.parse(builder_status, output)
        if not isinstance(result, Result):
            raise ValueError(
                "Parser class method parse(...) must return a Result based class"
            )
        return BuildResult(result, output)

    @abstractmethod
    def parse(self, builder_status, output: str) -> Result:
        """
        Parse the output of the builder. Method must return a Result instance
        or a Result based class (e.g Failure, SKipped).
        """
        pass


class DefaultParser(Parser):
    """
    Default Builder parser. This parser only parse for basic error and warning
    log. Return a dictionary with all error and warning texts.
    """

    def parse(self, builder_status: int, output: str) -> Result:
        if builder_status >= Status.FAILURE:
            return Result(
                builder_status, message="Error(s) found while building"
            )
        return Result(0, message="No error(s) found")
