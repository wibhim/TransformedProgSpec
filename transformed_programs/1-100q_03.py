class Solution(object):

    def lengthOfLongestSubstring(var_1, var_2):
        var_3 = {}
        var_4, var_5 = (0, 0)
        for var_6 in range(len(var_2)):
            if var_2[var_6] in var_3:
                var_4 = max(var_3[var_2[var_6]], var_4)
            var_5 = max(var_5, var_6 - var_4 + 1)
            var_3[var_2[var_6]] = var_6 + 1
        return var_5