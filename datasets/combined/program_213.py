def simple_interest(
    principal: float, daily_interest_rate: float, days_between_payments: float
) -> float:
    """
    >>> simple_interest(18000.0, 0.06, 3)
    3240.0
    >>> simple_interest(0.5, 0.06, 3)
    0.09
    >>> simple_interest(18000.0, 0.01, 10)
    1800.0
    >>> simple_interest(18000.0, 0.0, 3)
    0.0
    >>> simple_interest(5500.0, 0.01, 100)
    5500.0
    >>> simple_interest(10000.0, -0.06, 3)
    Traceback (most recent call last):
        ...
    ValueError: daily_interest_rate must be >= 0
    >>> simple_interest(-10000.0, 0.06, 3)
    Traceback (most recent call last):
        ...
    ValueError: principal must be > 0
    >>> simple_interest(5500.0, 0.01, -5)
    Traceback (most recent call last):
        ...
    ValueError: days_between_payments must be > 0
    """
    if days_between_payments <= 0:
        raise ValueError("days_between_payments must be > 0")
    if daily_interest_rate < 0:
        raise ValueError("daily_interest_rate must be >= 0")
    if principal <= 0:
        raise ValueError("principal must be > 0")
    return principal * daily_interest_rate * days_between_payments
