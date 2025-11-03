def generate_sum_of_subsets_solutions(nums: list[int], max_sum: int) -> list[list[int]]:
    """
    The main function. For list of numbers 'nums' find the subsets with sum
    equal to 'max_sum'

    >>> generate_sum_of_subsets_solutions(nums=[3, 34, 4, 12, 5, 2], max_sum=9)
    [[3, 4, 2], [4, 5]]
    >>> generate_sum_of_subsets_solutions(nums=[3, 34, 4, 12, 5, 2], max_sum=3)
    [[3]]
    >>> generate_sum_of_subsets_solutions(nums=[3, 34, 4, 12, 5, 2], max_sum=1)
    []
    """

    result: list[list[int]] = []
    path: list[int] = []
    num_index = 0
    remaining_nums_sum = sum(nums)
    create_state_space_tree(nums, max_sum, num_index, path, result, remaining_nums_sum)
    return result
