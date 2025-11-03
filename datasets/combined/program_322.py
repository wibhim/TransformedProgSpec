def sort_groups(groups):
    return sorted(groups, key=lambda g: (g.depth, g.priority, g.name))
