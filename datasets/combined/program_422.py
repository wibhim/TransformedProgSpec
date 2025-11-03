def is_tree_balanced(root):
	if root is None:
		return True
	lh = get_height(root.left)
	rh = get_height(root.right)
	if (abs(lh - rh) <= 1) and is_tree_balanced(
	root.left) is True and is_tree_balanced( root.right) is True:
		return True
	return False
