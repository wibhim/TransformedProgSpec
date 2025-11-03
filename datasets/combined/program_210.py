def toggle_middle_bits(n):
    if (n == 1):
        return 1
    return n ^ set_middle_bits(n)
