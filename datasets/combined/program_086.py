def get_factors(n):
    """[summary]

    Arguments:
        n {[int]} -- [to analysed number]

    Returns:
        [list of lists] -- [all factors of the number n]
    """

    def factor(n, i, combi, res):
        """[summary]
        helper function

        Arguments:
            n {[int]} -- [number]
            i {[int]} -- [to tested divisor]
            combi {[list]} -- [catch divisors]
            res {[list]} -- [all factors of the number n]

        Returns:
            [list] -- [res]
        """

        while i * i <= n:
            if n % i == 0:
                res += combi + [i, int(n/i)],
                factor(n/i, i, combi+[i], res)
            i += 1
        return res
    return factor(n, 2, [], [])
