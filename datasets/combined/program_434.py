def knapsack(
    weights: list, values: list, number_of_items: int, max_weight: int, index: int
) -> int:
    """
    Function description is as follows-
    :param weights: Take a list of weights
    :param values: Take a list of profits corresponding to the weights
    :param number_of_items: number of items available to pick from
    :param max_weight: Maximum weight that could be carried
    :param index: the element we are looking at
    :return: Maximum expected gain
    >>> knapsack([1, 2, 4, 5], [5, 4, 8, 6], 4, 5, 0)
    13
    >>> knapsack([3 ,4 , 5], [10, 9 , 8], 3, 25, 0)
    27
    """
    if index == number_of_items:
        return 0
    ans1 = 0
    ans2 = 0
    ans1 = knapsack(weights, values, number_of_items, max_weight, index + 1)
    if weights[index] <= max_weight:
        ans2 = values[index] + knapsack(
            weights, values, number_of_items, max_weight - weights[index], index + 1
        )
    return max(ans1, ans2)
