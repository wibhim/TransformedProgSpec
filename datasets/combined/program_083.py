def depth_first_search(graph: dict, vertex: int, visited: set, rec_stk: set) -> bool:
    """
    Recur for all neighbours.
    If any neighbour is visited and in rec_stk then graph is cyclic.
    >>> graph = {0:[], 1:[0, 3], 2:[0, 4], 3:[5], 4:[5], 5:[]}
    >>> vertex, visited, rec_stk = 0, set(), set()
    >>> depth_first_search(graph, vertex, visited, rec_stk)
    False
    """
    # Mark current node as visited and add to recursion stack
    visited.add(vertex)
    rec_stk.add(vertex)

    for node in graph[vertex]:
        if node not in visited:
            if depth_first_search(graph, node, visited, rec_stk):
                return True
        elif node in rec_stk:
            return True

    # The node needs to be removed from recursion stack before function ends
    rec_stk.remove(vertex)
    return False
