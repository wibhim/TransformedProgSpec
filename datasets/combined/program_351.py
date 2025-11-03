def lobb_num(n, m):
	return (((2 * m + 1) *
		binomial_coeff(2 * n, m + n))
					/ (m + n + 1))
