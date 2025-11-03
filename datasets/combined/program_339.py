def find_path(maze):
    cnt = dfs(maze, 0, 0, 0, -1)
    return cnt
