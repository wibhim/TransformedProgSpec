class Solution(object):

    def longestPalindrome(var_1, var_2):
        var_3 = [[0 for var_4 in range(len(var_2))] for var_4 in range(len(var_2))]
        var_5, var_6 = (1, '')
        for var_7 in range(len(var_2)):
            var_3[var_7][var_7] = 1
            var_6 = var_2[var_7]
        var_8 = 2
        while var_8 <= len(var_2):
            var_9 = 0
            while var_9 < len(var_2) - var_8 + 1:
                var_10 = var_9 + var_8 - 1
                if var_8 == 2 and var_2[var_9] == var_2[var_10]:
                    var_3[var_9][var_10] = 1
                    var_5 = max(var_5, 2)
                    var_6 = var_2[var_9:var_10 + 1]
                var_9 += 1
            var_8 += 1
        return var_6

class Solution(object):

    def longestPalindrome(var_1, var_2):

        def expand(var_2, var_11, var_12):
            while var_11 >= 0 and var_12 < len(var_2) and (var_2[var_11] == var_2[var_12]):
                var_11 -= 1
                var_12 += 1
            return var_12 - var_11 - 1
        var_13, var_14 = (0, 0)
        for var_7 in range(len(var_2)):
            var_15 = var_16(var_2, var_7, var_7 + 1)
            var_17 = var_16(var_2, var_7, var_7)
            var_8 = max(var_15, var_17)
            if var_8 > var_14 - var_13:
                var_13 = var_7 - (var_8 - 1) / 2
                var_14 = var_7 + var_8 / 2
        return var_2[var_13:var_14 + 1]