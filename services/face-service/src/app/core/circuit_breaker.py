"""Circuit breaker for AI API resilience (Google Cloud Vision, DeepFace)."""

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Callable, Optional, TypeVar, ParamSpec

import structlog

from .config import settings

logger = structlog.get_logger()

P = ParamSpec("P")
T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker for protecting external API calls.

    States:
    - CLOSED: Normal operation, calls pass through
    - OPEN: Circuit tripped, calls fail fast
    - HALF_OPEN: Testing recovery, limited calls allowed

    Usage:
        @circuit_breaker("google_vision")
        async def detect_faces(image_bytes: bytes) -> list[Face]:
            ...
    """

    name: str
    failure_threshold: int = field(default_factory=lambda: settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD)
    recovery_timeout: int = field(default_factory=lambda: settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT)

    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _last_failure_time: float = field(default=0.0, init=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for recovery timeout."""
        if self._state == CircuitState.OPEN:
            time_since_failure = time.time() - self._last_failure_time
            if time_since_failure >= self.recovery_timeout:
                return CircuitState.HALF_OPEN
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        return self.state == CircuitState.OPEN

    async def record_success(self) -> None:
        """Record successful call, potentially closing the circuit."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(
                    "Circuit breaker closing after recovery",
                    circuit=self.name,
                )
            self._state = CircuitState.CLOSED
            self._failure_count = 0

    async def record_failure(self, error: Optional[Exception] = None) -> None:
        """Record failed call, potentially opening the circuit."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(
                    "Circuit breaker opened",
                    circuit=self.name,
                    failures=self._failure_count,
                    error=str(error) if error else None,
                )

    def reset(self) -> None:
        """Reset circuit breaker to initial state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, circuit_name: str, retry_after: float):
        self.circuit_name = circuit_name
        self.retry_after = retry_after
        super().__init__(f"Circuit '{circuit_name}' is open, retry after {retry_after:.1f}s")


# Registry of circuit breakers
_circuits: dict[str, CircuitBreaker] = {}


def get_circuit(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in _circuits:
        _circuits[name] = CircuitBreaker(name=name)
    return _circuits[name]


def circuit_breaker(name: str) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator to wrap a function with circuit breaker protection.

    Usage:
        @circuit_breaker("google_vision")
        async def call_vision_api(image: bytes) -> dict:
            ...
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            cb = get_circuit(name)

            # Check if circuit is open
            if cb.is_open:
                retry_after = cb.recovery_timeout - (time.time() - cb._last_failure_time)
                raise CircuitOpenError(name, max(0, retry_after))

            try:
                result = await func(*args, **kwargs)
                await cb.record_success()
                return result
            except Exception as e:
                await cb.record_failure(e)
                raise

        return wrapper

    return decorator
