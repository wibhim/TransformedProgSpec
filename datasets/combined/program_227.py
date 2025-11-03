def min_steps_to_one(number: int) -> int:
    """
    Minimum steps to 1 implemented using tabulation.
    >>> min_steps_to_one(10)
    3
    >>> min_steps_to_one(15)
    4
    >>> min_steps_to_one(6)
    2

    :param number:
    :return int:
    """

    if number <= 0:
        msg = f"n must be greater than 0. Got n = {number}"
        raise ValueError(msg)

    table = [number + 1] * (number + 1)

    # starting position
    table[1] = 0
    for i in range(1, number):
        table[i + 1] = min(table[i + 1], table[i] + 1)
        # check if out of bounds
        if i * 2 <= number:
            table[i * 2] = min(table[i * 2], table[i] + 1)
        # check if out of bounds
        if i * 3 <= number:
            table[i * 3] = min(table[i * 3], table[i] + 1)
    return table[number]
