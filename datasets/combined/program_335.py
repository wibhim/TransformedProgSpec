def gcd(p,q):
    while q != 0:
        p, q = q,p%q
    return p
