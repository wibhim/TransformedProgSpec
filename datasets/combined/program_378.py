def permute_unique(nums):
    perms = [[]]
    for n in nums:
        new_perms = []
        for l in perms:
            for i in range(len(l)+1):
                new_perms.append(l[:i]+[n]+l[i:])
                if i < len(l) and l[i] == n:
                    break  # handles duplication
        perms = new_perms
    return perms
