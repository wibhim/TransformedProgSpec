def tree_broadcast_time(G, node=None):
    """Return the minimum broadcast time of a (node in a) tree.

    The minimum broadcast time of a node is defined as the minimum amount
    of time required to complete broadcasting starting from that node.
    The broadcast time of a graph is the maximum over
    all nodes of the minimum broadcast time from that node [1]_.
    This function returns the minimum broadcast time of `node`.
    If `node` is `None`, the broadcast time for the graph is returned.

    Parameters
    ----------
    G : Graph
        The graph should be an undirected tree.

    node : node, optional (default=None)
        Starting node for the broadcasting. If `None`, the algorithm
        returns the broadcast time of the graph instead.

    Returns
    -------
    int
        Minimum broadcast time of `node` in `G`, or broadcast time of `G`
        if no node is provided.

    Raises
    ------
    NetworkXNotImplemented
        If `G` is directed or is a multigraph.

    NodeNotFound
        If `node` is not a node in `G`.

    NotATree
        If `G` is not a tree.

    References
    ----------
    .. [1] Harutyunyan, H. A. and Li, Z.
        "A Simple Construction of Broadcast Graphs."
        In Computing and Combinatorics. COCOON 2019
        (Ed. D. Z. Du and C. Tian.) Springer, pp. 240-253, 2019.
    """
    if node is not None and node not in G:
        err = f"node {node} not in G"
        raise nx.NodeNotFound(err)
    b_T, b_C = tree_broadcast_center(G)
    if node is None:
        return b_T + sum(1 for _ in nx.bfs_layers(G, b_C)) - 1
    return b_T + next(
        d for d, layer in enumerate(nx.bfs_layers(G, b_C)) if node in layer
    )
