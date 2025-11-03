def flatten(test_tuple):
	for tup in test_tuple:
		if isinstance(tup, tuple):
			yield from flatten(tup)
		else:
			yield tup
