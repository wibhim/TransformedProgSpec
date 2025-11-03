def common_prefix (arr, n):
	prefix = arr[0]
	for i in range (1, n):
		prefix = common_prefix_util(prefix, arr[i])
	return (prefix)
