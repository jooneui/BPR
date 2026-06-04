"""Backward-compatibility redirect module.

This module no longer contains any functions. All former contents have
been redistributed to their logical homes:

- Pipeline plumbing  → pipeline.py
- Stage 1 plotting   → plotting_stage1.py
- Stage 2 plotting   → plotting_stage2.py
- Stage 3 plotting   → plotting_stage3.py
- Legacy / dead code → _legacy.py (opt-in only)

If you imported from traffic_utils._helpers, update your imports to
use the new module names. For legacy code, use::

    from traffic_utils._legacy import *
"""
