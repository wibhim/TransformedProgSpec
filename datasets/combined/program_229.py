def num_islands(grid):
    count = 0
    for i in range(len(grid)):
        for j, col in enumerate(grid[i]):
            if col == 1:
                dfs(grid, i, j)
                count += 1
    return count
