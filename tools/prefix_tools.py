from __future__ import annotations

import ipaddress


def canonical_prefix(cidr: str) -> str:
    """Return a CIDR prefix in canonical **IPv4 network form**.

    Canonicalization clears any host bits while preserving the prefix length.

    Args:
        cidr: An IPv4 address and prefix length in CIDR notation.

    Returns:
        The canonical network address and prefix length in CIDR notation.

    Raises:
        ValueError: If ``cidr`` is not a valid IPv4 network specification.

    Examples:
        >>> canonical_prefix("10.1.7.9/24")
        '10.1.7.0/24'
        >>> canonical_prefix("192.0.2.8/32")
        '192.0.2.8/32'

    Implementation notes:
        Host bits in the input are allowed, so parsing must not require the
        supplied address to already be a network address. Return a string,
        rather than an ``IPv4Network`` object.
    
    Hint:
        You can use Python's standard-library ``ipaddress`` module.
    """
    return str(ipaddress.IPv4Network(cidr, strict=False))


def prefix_contains(cidr: str, ip: str) -> bool:
    """Return whether an IPv4 address belongs to a CIDR prefix.

    Args:
        cidr: An IPv4 network in CIDR notation. Host bits are permitted.
        ip: The IPv4 address whose membership should be tested.

    Returns:
        ``True`` if ``ip`` belongs to ``cidr``; otherwise, ``False``.

    Raises:
        ValueError: If either argument is not valid IPv4 input.

    Examples:
        >>> prefix_contains("10.1.0.0/16", "10.1.200.7")
        True
        >>> prefix_contains("10.1.0.0/16", "10.2.0.1")
        False
        >>> prefix_contains("0.0.0.0/0", "203.0.113.99")
        True

    Implementation notes:
        Treat ``cidr`` as a network even when its address has host bits. Both
        inputs must be interpreted as IPv4, rather than allowing IPv6 values.

    Hint:
        You can use Python's standard-library ``ipaddress`` module.
        Network objects support membership tests with Python's 
        ``in`` operator.
    """
    cidr = ipaddress.IPv4Network(cidr, strict=False)
    ip = ipaddress.IPv4Address(ip)

    return ip in cidr


def prefix_length(cidr: str) -> int:
    """Return the prefix length of a validated IPv4 CIDR prefix.

    Args:
        cidr: An IPv4 network in CIDR notation. Host bits are permitted.

    Returns:
        The prefix length as an integer from 0 through 32, inclusive.

    Raises:
        ValueError: If ``cidr`` is not a valid IPv4 network specification.

    Examples:
        >>> prefix_length("10.1.7.9/24")
        24
        >>> prefix_length("0.0.0.0/0")
        0
        >>> prefix_length("192.0.2.8/32")
        32

    Hint:
        You can use Python's standard-library ``ipaddress`` module.
    """
    network = ipaddress.IPv4Network(cidr, False)
    return network.prefixlen

def longest_prefix_match(prefixes: list[str], destination_ip: str) -> str | None:
    """Return the matching CIDR prefix with the longest prefix length.

    Args:
        prefixes: Candidate IPv4 prefixes in CIDR notation. Host bits are
            permitted and the list may be empty.
        destination_ip: The IPv4 destination address to match.

    Returns:
        The most-specific matching prefix in canonical CIDR notation, or
        ``None`` if no prefix matches.

    Raises:
        ValueError: If the destination or any candidate prefix is not valid
            IPv4 input.

    Examples:
        >>> routes = [
        ...     "0.0.0.0/0",
        ...     "10.0.0.0/8",
        ...     "10.4.0.0/16",
        ...     "10.4.32.0/20",
        ... ]
        >>> longest_prefix_match(routes, "10.4.35.7")
        '10.4.32.0/20'
        >>> longest_prefix_match(routes, "8.8.8.8")
        '0.0.0.0/0'
        >>> longest_prefix_match(["192.0.2.0/24"], "203.0.113.1") is None
        True

    Implementation notes:
        Examine every candidate because input order does not determine
        specificity. Track both the best canonical prefix and its length, 
        ensuring that a ``/0`` route can be selected.

    Hint:
        You can use Python's standard-library ``ipaddress`` module.
    """
    longest_prefix = None
    longest_length = -1
    for prefix in prefixes:
        curr_length = prefix_length(prefix)
        if prefix_contains(prefix, destination_ip) and curr_length > longest_length:
            longest_prefix = prefix
            longest_length = curr_length

    if longest_prefix:
        return canonical_prefix(longest_prefix)
    
    return None
