def combination_sum(candidates, target):

    def dfs(nums, target, index, path, res):
        if target < 0:
            return  # backtracking
        if target == 0:
            res.append(path)
            return
        for i in range(index, len(nums)):
            dfs(nums, target-nums[i], i, path+[nums[i]], res)

    res = []
    candidates.sort()
    dfs(candidates, target, 0, [], res)
    return res
