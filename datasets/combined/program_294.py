def pacific_atlantic(matrix):
    """
    :type matrix: List[List[int]]
    :rtype: List[List[int]]
    """
    n = len(matrix)
    if not n: return []
    m = len(matrix[0])
    if not m: return []
    res = []
    atlantic = [[False for _ in range (n)] for _ in range(m)]
    pacific =  [[False for _ in range (n)] for _ in range(m)]
    for i in range(n):
        dfs(pacific, matrix, float("-inf"), i, 0)
        dfs(atlantic, matrix, float("-inf"), i, m-1)
    for i in range(m):
        dfs(pacific, matrix, float("-inf"), 0, i)
        dfs(atlantic, matrix, float("-inf"), n-1, i)
    for i in range(n):
        for j in range(m):
            if pacific[i][j] and atlantic[i][j]:
                res.append([i, j])
    return res
