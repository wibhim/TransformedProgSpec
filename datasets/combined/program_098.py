def max_height(node):
	if node is None:
		return 0 ;
	else :
		left_height = max_height(node.left)
		right_height = max_height(node.right)
		if (left_height > right_height):
			return left_height+1
		else:
			return right_height+1
