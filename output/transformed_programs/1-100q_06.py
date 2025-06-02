class Solution(object):

    def convert(var_1, var_2, var_3):
        if var_3 == 1:
            return var_2
        var_4 = ['' for var_5 in range(var_3)]
        var_6, var_7 = (0, 1)
        for var_8 in var_2:
            var_4[var_6] += var_8
            if var_6 == var_3 - 1:
                var_7 = 0
            if var_6 == 0:
                var_7 = 1
            if var_7:
                var_6 += 1
        var_9 = ''
        for var_10 in var_4:
            var_9 += var_10
        return var_9
print(Solution().convert('PAYPALISHIRING', 3))