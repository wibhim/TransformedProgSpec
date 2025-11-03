def maze_search(maze):
    BLOCKED, ALLOWED = 0, 1
    UNVISITED, VISITED = 0, 1

    initial_x, initial_y = 0, 0

    if maze[initial_x][initial_y] == BLOCKED:
        return -1

    directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]

    height, width = len(maze), len(maze[0])

    target_x, target_y = height - 1, width - 1

    queue = deque([(initial_x, initial_y, 0)])

    is_visited = [[UNVISITED for w in range(width)] for h in range(height)]
    is_visited[initial_x][initial_y] = VISITED

    while queue:
        x, y, steps = queue.popleft()

        if x == target_x and y == target_y:
            return steps

        for dx, dy in directions:
            new_x = x + dx
            new_y = y + dy

            if not (0 <= new_x < height and 0 <= new_y < width):
                continue

            if maze[new_x][new_y] == ALLOWED and is_visited[new_x][new_y] == UNVISITED:
                queue.append((new_x, new_y, steps + 1))
                is_visited[new_x][new_y] = VISITED

    return -1
