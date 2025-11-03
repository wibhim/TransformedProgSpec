import math

def get_Pos_Of_Right_most_Set_Bit(n):
    return int(math.log2(n&-n)+1)
