def dfs(graph: dict, vert: int, visited: list) -> list:
    """
    Use depth first search to find all vertices
    being in the same component as initial vertex
    >>> dfs(test_graph_1, 0, 5 * [False])
    [0, 1, 3, 2]
    >>> dfs(test_graph_2, 0, 6 * [False])
    [0, 1, 3, 2]
    """

    visited[vert] = True
    connected_verts = []

    for neighbour in graph[vert]:
        if not visited[neighbour]:
            connected_verts += dfs(graph, neighbour, visited)

    return [vert, *connected_verts]
