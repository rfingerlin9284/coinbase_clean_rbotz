"""Project-level stochastic helpers.

All randomness in the project should go through this module. By default it uses
cryptographically secure entropy and non-deterministic timestamps. Deterministic
mode has been removed; this module provides non-deterministic entropy by
default.
"""
import os
import secrets
import time
import hashlib
from typing import Sequence, Any


def random_bytes(n: int = 16) -> bytes:
    """Return cryptographically secure random bytes.

    Deterministic mode has been removed — calls receive entropy via
    `secrets.token_bytes` to reflect the project's stochastic-first policy.
    """
    return secrets.token_bytes(n)


def random_hex(n: int = 16) -> str:
    return random_bytes(n).hex()


def random_choice(seq: Sequence[Any]) -> Any:
    """Choose an element from `seq` using secure entropy.

    This uses non-deterministic selection (no deterministic opt-in by default).
    """
    if not seq:
        raise IndexError("Cannot choose from empty sequence")
    return secrets.choice(seq)
