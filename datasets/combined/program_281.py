def find_lcm(num1, num2):
	if(num1>num2):
		num = num1
		den = num2
	else:
		num = num2
		den = num1
	rem = num % den
	while (rem != 0):
		num = den
		den = rem
		rem = num % den
	gcd = den
	lcm = int(int(num1 * num2)/int(gcd))
	return lcm
