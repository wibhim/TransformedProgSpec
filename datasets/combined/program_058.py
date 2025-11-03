def largest_pow_of_two_le_num(number: int) -> int:
    """
    Return the largest power of two less than or equal to a number.

    >>> largest_pow_of_two_le_num(0)
    0
    >>> largest_pow_of_two_le_num(1)
    1
    >>> largest_pow_of_two_le_num(-1)
    0
    >>> largest_pow_of_two_le_num(3)
    2
    >>> largest_pow_of_two_le_num(15)
    8
    >>> largest_pow_of_two_le_num(99)
    64
    >>> largest_pow_of_two_le_num(178)
    128
    >>> largest_pow_of_two_le_num(999999)
    524288
    >>> largest_pow_of_two_le_num(99.9)
    Traceback (most recent call last):
        ...
    TypeError: Input value must be a 'int' type
    """
    if isinstance(number, float):
        raise TypeError("Input value must be a 'int' type")
    if number <= 0:
        return 0
    res = 1
    while (res << 1) <= number:
        res <<= 1
    return res
