def lcp_w_suffix_str(array, s):
	N = len(array)

	lcp_array = [0]*N
	inv_suffix = [0]*N

	for index in range(N):
		inv_suffix[array[index]] = index

	maxLen = 0

	for index in range(N):
		if inv_suffix[index] == N-1:
			maxLen = 0
			continue

		index_j = array[inv_suffix[index]+1]
		while(index+maxLen < N and index_j+maxLen < N and s[index+maxLen] == s[index_j+maxLen]):
			maxLen += 1

		lcp_array[inv_suffix[index]] = maxLen

		if maxLen > 0:
			maxLen -= 1

	return lcp_array
