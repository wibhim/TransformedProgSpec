def removals(arr, n, k):
	ans = n - 1
	arr.sort()
	for i in range(0, n):
		j = find_ind(arr[i], i,
					n, k, arr)
		if (j != -1):
			ans = min(ans, n -
						(j - i + 1))
	return ans
