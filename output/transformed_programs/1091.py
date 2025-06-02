class Solution(object):

    def shortestPathBinaryMatrix(var_1, var_2):
        if not var_2:
            return -1
        var_3, var_4 = (len(var_2), len(var_2[0]))
        if var_2[0][0] or var_2[var_3 - 1][var_4 - 1]:
            return -1
        var_5 = [[0, 0, 1]]
        for var_6, var_7, var_8 in var_5:
            if var_6 == var_3 - 1 and var_7 == var_4 - 1:
                return var_8
            for var_9, var_10 in [(-1, -1), (0, -1), (-1, 1), (-1, 0), (1, 0), (1, -1), (0, 1), (1, 1)]:
                var_11, var_12 = (var_6 + var_9, var_7 + var_10)
                if 0 <= var_11 < var_3 and 0 <= var_12 < var_4 and (not var_2[var_11][var_12]):
                    var_2[var_11][var_12] = 1
                    queue.append([n_row, n_col, dist + 1])
        return -1