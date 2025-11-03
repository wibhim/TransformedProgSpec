def generate_parenthesis_v2(n):
    def add_pair(res, s, left, right):
        if left == 0 and right == 0:
            res.append(s)
        if left > 0:
            add_pair(res, s + "(", left - 1, right)
        if right > 0 and left < right:
            add_pair(res, s + ")", left, right - 1)

    res = []
    add_pair(res, "", n, n)
    return res
