import codecs
import sys

from typing import Any, AnyStr, Optional, Union


def safe_decode(s: Union[AnyStr, None]) -> Optional[str]:
    """Safely decodes a binary string to unicode"""
    if isinstance(s, str):
        return s
    elif isinstance(s, bytes):
        return s.decode(sys.getfilesystemencoding(), "surrogateescape")
    elif s is None:
        return None
    else:
        raise TypeError("Expected bytes or text, but got %r" % (s,))


def to_text(obj: Any, encoding: str = "utf-8", nonstring="simplerepr"):
    """Make sure that a string is a text string

    :returns: Typically this returns a text string. If a nonstring object is
        passed in this may be a different type depending on the strategy
        specified by nonstring.  This will never return a byte string.

    """
    if isinstance(obj, str):
        return obj

    if isinstance(obj, bytes):
        try:
            codecs.lookup_error("surrogateescape")
            errors = "surrogateescape"
        except LookupError:
            errors = "strict"
        return obj.decode(encoding, errors=errors)

    if nonstring == "simplerepr":
        try:
            value = str(obj)
        except UnicodeError:
            try:
                value = repr(obj)
            except UnicodeError:
                return ""
    elif nonstring == "passthru":
        return obj

    return to_text(value, encoding)


def to_bytes(obj: Union[str, bytes]):
    """Make sure that a string is a byte string"""
    if isinstance(obj, bytes):
        return obj

    original_errors = None
    if isinstance(obj, str):
        try:
            # Try this first as it's the fastest
            return obj.encode("utf-8")
        except UnicodeEncodeError:
            if original_errors in (None, "surrogate_then_replace"):
                # We should only reach this if encoding was non-utf8 original_errors was
                # surrogate_then_escape and errors was surrogateescape

                # Slow but works
                return_string = obj.encode("utf-8", "surrogateescape")
                return_string = return_string.decode("utf-8", "replace")
                return return_string.encode("utf-8", "replace")
            raise

    try:
        value = str(obj)
    except UnicodeError:
        try:
            value = repr(obj)
        except UnicodeError:
            # Giving up
            return to_bytes("")

    return to_bytes(value)
