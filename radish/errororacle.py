# -*- coding: utf-8 -*-

"""
    This module provides some functionality to diagnose thrown exceptions
"""


import sys
import os
from functools import wraps

from colorful import colorful

from .terrain import world
from .exceptions import RadishError, FeatureFileSyntaxError, StepDefinitionNotFoundError, HookError, SameStepError
from .utils import Failure


__RADISH_DOC__ = "https://github.com/radish-bdd/radish"


def write(text):
    """
        Writes the given text to the console
    """
    print(text)


def write_error(text):
    """
        Writes the given text to the console
    """
    write("{0}: {1}".format(colorful.bold_red("Error"), colorful.red(text)))


def write_failure(failure):
    """
        Writes the failure to the console
    """
    write("\n{0}".format(colorful.red(failure.traceback)))


def abort(return_code):
    """
        Aborts the program with the given return_code
    """
    sys.exit(return_code)


def debug_enabled():
    """
        Return True is ``RADISH_DEBUG`` environmental variable is set to 1
    """
    return 'RADISH_DEBUG' in os.environ and os.environ['RADISH_DEBUG'] == "1"


def enable_excepthook():
    """
        Enable Radish custom excepthook handling system-wide if debug
        is not set. Specifically this sets ``sys.excepthook`` to
        ``oracleerror.catch_unhandled_exception``.
    """

    if debug_enabled() is False:
        sys.excepthook = catch_unhandled_exception


def error_oracle(func):
    """
        Decorator to diagnose thrown exceptions. Only enabled if debug is
        enabled (see ``debug_enabled()``)
    """

    if debug_enabled():
        return func

    @wraps(func)
    def _decorator(*args, **kwargs):
        """
            The actual decorator
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:  # pylint: disable=broad-except
            handle_exception(e)

    return _decorator


def catch_unhandled_exception(exc_type, exc_value, traceback):
    """
        Catch all unhandled exceptions
    """
    handle_exception(exc_value)


def handle_exception(exception):
    """
        Handle the given exception

        This will print more information about the given exception

        :param Exception exception: the exception to handle
    """
    if isinstance(exception, HookError):
        write_error(exception)
        write_failure(exception.failure)
        abort(1)
    elif isinstance(exception, RadishError):
        write_error(exception)
        abort(1)
    elif isinstance(exception, KeyboardInterrupt):
        write("Aborted by the user...")
        abort(1)
    else:
        write_error(exception)
        write_failure(Failure(exception))
        abort(2)
