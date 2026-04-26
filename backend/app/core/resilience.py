"""
Resilience patterns for User Management Portal.

This module provides retry logic, circuit breaker pattern,
and other resilience mechanisms.

GitHub Issue: HLD-005
"""

import asyncio
import random
import logging
from enum import Enum, auto
from datetime import datetime, timedelta
from typing import Callable, Type, Tuple, Optional, Dict
from functools import wraps

from app.core.errors import CircuitBreakerOpenError

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_retries: int = 3,
        strategy: str = "exponential",
        base_delay: float = 0.1,
        max_delay: float = 10.0,
        exceptions: Tuple[Type[Exception], ...] = (Exception,),
        jitter: bool = True
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts
            strategy: Retry strategy (exponential, linear, immediate)
            base_delay: Base delay between retries in seconds
            max_delay: Maximum delay between retries
            exceptions: Tuple of exceptions to catch and retry
            jitter: Whether to add random jitter to delay
        """
        self.max_retries = max_retries
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exceptions = exceptions
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for retry attempt.
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        if self.strategy == "exponential":
            delay = self.base_delay * (2 ** attempt)
        elif self.strategy == "linear":
            delay = self.base_delay * (attempt + 1)
        else:  # immediate
            delay = self.base_delay
        
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return min(delay, self.max_delay)


def retry(config: Optional[RetryConfig] = None):
    """
    Decorator for retry logic.
    
    Args:
        config: Retry configuration
        
    Example:
        @retry(RetryConfig(max_retries=3, strategy="exponential"))
        async def fetch_data():
            return await api.get_data()
    """
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except config.exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_retries:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                            f"after {delay:.2f}s: {str(e)}"
                        )
                        await asyncio.sleep(delay)
            
            raise last_exception
        
        return wrapper
    return decorator


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = auto()      # Normal operation
    OPEN = auto()        # Failing, reject requests
    HALF_OPEN = auto()   # Testing if recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Prevents cascading failures by stopping requests to failing services.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        half_open_max_calls: int = 3,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            name: Circuit breaker identifier
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            half_open_max_calls: Max calls in half-open state
            expected_exception: Exception type to count as failure
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.expected_exception = expected_exception
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_calls = 0
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Original exception if function fails
        """
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_calls = 0
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is OPEN"
                    )
            
            if self.state == CircuitState.HALF_OPEN:
                if self.half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' half-open limit reached"
                    )
                self.half_open_calls += 1
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except self.expected_exception as e:
            await self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery."""
        if self.last_failure_time is None:
            return True
        return datetime.utcnow() - self.last_failure_time >= timedelta(
            seconds=self.recovery_timeout
        )
    
    async def _on_success(self):
        """Handle successful call."""
        async with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.half_open_max_calls:
                    self._reset()
            else:
                self.failure_count = 0
    
    async def _on_failure(self):
        """Handle failed call."""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.utcnow()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
            elif self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(
                    f"Circuit breaker '{self.name}' opened after "
                    f"{self.failure_count} failures"
                )
    
    def _reset(self):
        """Reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.last_failure_time = None
        logger.info(f"Circuit breaker '{self.name}' reset to CLOSED")
    
    @property
    def is_open(self) -> bool:
        """Check if circuit is open."""
        return self.state == CircuitState.OPEN
    
    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed."""
        return self.state == CircuitState.CLOSED
    
    def get_stats(self) -> Dict:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.name,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


# Pre-configured circuit breakers
CIRCUIT_BREAKERS: Dict[str, CircuitBreaker] = {
    "email_service": CircuitBreaker(
        name="email_service",
        failure_threshold=5,
        recovery_timeout=30,
        half_open_max_calls=3
    ),
    "sms_service": CircuitBreaker(
        name="sms_service",
        failure_threshold=3,
        recovery_timeout=60,
        half_open_max_calls=2
    ),
    "notification_service": CircuitBreaker(
        name="notification_service",
        failure_threshold=5,
        recovery_timeout=30,
        half_open_max_calls=3
    )
}


def circuit_breaker(breaker_name: str):
    """
    Decorator for circuit breaker pattern.
    
    Args:
        breaker_name: Name of circuit breaker to use
        
    Example:
        @circuit_breaker("email_service")
        async def send_email(to: str, subject: str, body: str):
            return await email_client.send(to, subject, body)
    """
    breaker = CIRCUIT_BREAKERS[breaker_name]
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Pre-configured retry configs for common scenarios
RETRY_CONFIGS = {
    "database": RetryConfig(
        max_retries=3,
        strategy="exponential",
        base_delay=0.1,
        exceptions=(ConnectionError, TimeoutError)
    ),
    "redis": RetryConfig(
        max_retries=2,
        strategy="immediate",
        base_delay=0.05,
        exceptions=(ConnectionError, TimeoutError)
    ),
    "email": RetryConfig(
        max_retries=5,
        strategy="linear",
        base_delay=1.0,
        jitter=True,
        exceptions=(Exception,)
    ),
    "external_api": RetryConfig(
        max_retries=3,
        strategy="exponential",
        base_delay=0.5,
        jitter=True,
        exceptions=(Exception,)
    )
}
