# COPY-FORWARD FILE FROM PA1.
# This starter is intentionally the PA1 skeleton. Do not reimplement LPM for PA2.
# Run: python3 tools/import_pa1.py /path/to/your/PA1/repository

from __future__ import annotations

import ipaddress


def canonical_prefix(cidr: str) -> str:
    """Return cidr in canonical IPv4 network form, e.g. 10.1.7.9/24 -> 10.1.7.0/24."""
    # TODO: Part II
    raise NotImplementedError


def prefix_contains(cidr: str, ip: str) -> bool:
    """Return True iff IPv4 address ip belongs to cidr."""
    # TODO: Part II
    raise NotImplementedError


def prefix_length(cidr: str) -> int:
    """Return the prefix length of cidr after validating it as IPv4."""
    # TODO: Part II
    raise NotImplementedError


def longest_prefix_match(prefixes: list[str], destination_ip: str) -> str | None:
    """Return the matching CIDR prefix with the longest prefix length.

    Return None if no prefix matches. The function must work for /0 through
    /32 and must not depend on the order in which different-length prefixes
    are supplied.
    """
    # TODO: Part II
    raise NotImplementedError
