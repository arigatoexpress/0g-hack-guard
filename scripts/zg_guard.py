#!/usr/bin/env python3
"""Thin repo-local wrapper for the zg-guard CLI."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from zg_hack_guard.cli import main

if __name__ == "__main__":
    sys.exit(main())
