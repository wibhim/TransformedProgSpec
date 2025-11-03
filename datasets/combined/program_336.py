def palindromic_substrings_iter(s):
    """
    A slightly more Pythonic approach with a recursive generator
    """
    if not s:
        yield []
        return
    for i in range(len(s), 0, -1):
        sub = s[:i]
        if sub == sub[::-1]:
            for rest in palindromic_substrings_iter(s[i:]):
                yield [sub] + rest
