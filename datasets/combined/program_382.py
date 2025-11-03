def min_flip_to_make_string_alternate(str):
	return min(get_flip_with_starting_charcter(str, '0'),get_flip_with_starting_charcter(str, '1'))
