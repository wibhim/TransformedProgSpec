def recursive_get_factors(n):

    def factor(n, i, combi, combis):
        while i * i <= n:
            if n % i == 0:
                combis.append(combi + [i, n//i]),
                factor(n//i, i, combi+[i], combis)
            i += 1
        return combis

    return factor(n, 2, [], [])
