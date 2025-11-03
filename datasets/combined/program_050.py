def bin_coff(n, r):
	val = 1
	if (r > (n - r)):
		r = (n - r)
	for i in range(0, r):
		val *= (n - i)
		val //= (i + 1)
	return val
