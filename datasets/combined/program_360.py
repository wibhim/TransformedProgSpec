def binomial_probability(n, k, p):
	return (nCr(n, k) * pow(p, k) *	pow(1 - p, n - k))
