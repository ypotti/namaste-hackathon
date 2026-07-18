"""LangGraph-powered math puzzle page generator."""

import logging

# Package-level logger. Handlers are configured by cli.py (or the caller).
# Using getLogger here means all sub-modules just do:
#   log = logging.getLogger(__name__)
# and their messages bubble up through this root logger.
log = logging.getLogger(__name__)
