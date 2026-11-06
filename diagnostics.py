import os
import sys


_RED = "\033[31;1m"
_RESET = "\033[0m"


def supports_color(stream):
    return os.environ.get("NO_COLOR") is None and bool(
        getattr(stream, "isatty", lambda: False)()
    )


def format_diagnostic(error, color=False):
    message = f"{type(error).__name__}: {error}"
    if color:
        return f"{_RED}{message}{_RESET}"
    return message


def print_diagnostic(error, stream=None):
    stream = stream or sys.stderr
    print(format_diagnostic(error, color=supports_color(stream)), file=stream)
