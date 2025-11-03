def toggle_F_and_L_bits(n) :
    if (n == 1) :
        return 0
    return n ^ take_L_and_F_set_bits(n)
