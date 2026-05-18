# SPDX-FileCopyrightText: 2026 Luis N.
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""Suppress noisy ADK / google-genai warnings for CLI and HTTP runners.

Import this module before any ``google.adk`` or ``google.genai`` imports.
"""

from __future__ import annotations

import logging
import os
import warnings

_CONFIGURED = False


class _DropGenaiNonTextPartsLog(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        return "there are non-text parts in the response:" not in record.getMessage()


def configure_quiet_warnings() -> None:
    """Idempotent: filters genai mixed-part noise and ADK experimental UserWarnings."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    # google-genai logs (not warnings.warn) when .text is read on function_call responses.
    for logger_name in ("google_genai.types", "google.genai.types"):
        logging.getLogger(logger_name).addFilter(_DropGenaiNonTextPartsLog())

    warnings.filterwarnings("ignore", message=".*non-text parts.*")
    warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*feature.*", module=r"google\.adk\.features\..*")

    # ADK reads this env var; default on when unset (docker-compose sets it explicitly).
    if "ADK_SUPPRESS_EXPERIMENTAL_FEATURE_WARNINGS" not in os.environ:
        os.environ["ADK_SUPPRESS_EXPERIMENTAL_FEATURE_WARNINGS"] = "true"
