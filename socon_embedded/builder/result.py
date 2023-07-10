from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from socon_embedded.builder import BuildInfo


class Status:
    PASS: int = 0
    FAILURE: int = 1
    SKIPPED: int = -1


@dataclass
class Result:
    status_code: int = Status.PASS
    message: Optional[str] = None
    text: Optional[str] = None


class BuildResult:
    """Base class that stores build result"""

    def __init__(
        self,
        result: Result,
        output: Optional[str] = None
    ) -> None:
        self.result = result
        self.output = output
        self.build_info: BuildInfo = None
        self.execution_time: Union[float, int] = 0

    @property
    def is_skipped(self) -> bool:
        """Is the result is pass or fail"""
        return self.result.status_code <= Status.SKIPPED

    @property
    def is_fail(self) -> bool:
        """Is the result is pass or fail"""
        return self.result.status_code >= Status.FAILURE

    def get_status_message(self) -> str:
        if self.is_fail:
            return 'FAIL'
        elif self.is_skipped:
            return 'SKIPPED'
        return 'PASS'
