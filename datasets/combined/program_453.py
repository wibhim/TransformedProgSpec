def prefix_sum(array: list[int], queries: list[tuple[int, int]]) -> list[int]:
    """
    >>> prefix_sum([1, 4, 6, 2, 61, 12], [(2, 5), (1, 5), (3, 4)])
    [81, 85, 63]
    >>> prefix_sum([4, 2, 1, 6, 3], [(3, 4), (1, 3), (0, 2)])
    [9, 9, 7]
    """
    # The prefix sum array
    dp = [0] * len(array)
    dp[0] = array[0]
    for i in range(1, len(array)):
        dp[i] = dp[i - 1] + array[i]

    # See Algorithm section (Line 44)
    result = []
    for query in queries:
        left, right = query
        res = dp[right]
        if left > 0:
            res -= dp[left - 1]
        result.append(res)

    return result
