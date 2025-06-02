// Dafny Specification and Program for the given Python code

method ThreeSum(nums: seq<int>) returns (res: seq<seq<int>>)
    requires true
    ensures
        // Each element in res is a triple of indices in nums whose sum is 0
        forall t :: 0 <= t < |res| ==>
            |res[t]| == 3 &&
            res[t][0] + res[t][1] + res[t][2] == 0
    ensures
        // All triples in res are unique (no duplicates)
        forall i, j :: 0 <= i < j < |res| ==> res[i] != res[j]
    ensures
        // All returned triples are present in nums
        forall t :: 0 <= t < |res| ==>
            exists i, j, k :: 
                0 <= i < j < k < |nums| &&
                multiset{nums[i], nums[j], nums[k]} == multiset{res[t][0], res[t][1], res[t][2]}
{
    var n := |nums|;
    var arr := nums[..];
    // Sort the array
    var sortedNums := arr[..];
    sortedNums := Sort(sortedNums);

    if n >= 3 && sortedNums[0] == sortedNums[n - 1] && sortedNums[0] == 0 {
        res := [ [0, 0, 0] ];
        return;
    }

    var resultSet := set seq<int>{};
    var resultList := new seq<seq<int>>[0];

    var index := 0;
    while index < n - 1
        invariant 0 <= index <= n - 1
        invariant forall t :: 0 <= t < |resultList| ==> |resultList[t]| == 3 && resultList[t][0] + resultList[t][1] + resultList[t][2] == 0
        invariant forall i, j :: 0 <= i < j < |resultList| ==> resultList[i] != resultList[j]
    {
        var left := index + 1;
        var right := n - 1;
        while left < right
            invariant index + 1 <= left <= right <= n - 1
            invariant forall t :: 0 <= t < |resultList| ==> |resultList[t]| == 3 && resultList[t][0] + resultList[t][1] + resultList[t][2] == 0
            invariant forall i, j :: 0 <= i < j < |resultList| ==> resultList[i] != resultList[j]
        {
            var currSum := sortedNums[index] + sortedNums[left] + sortedNums[right];
            if currSum == 0 {
                var triple := [sortedNums[index], sortedNums[left], sortedNums[right]];
                if !(triple in resultSet) {
                    resultSet := resultSet + {triple};
                    resultList := resultList + [triple];
                }
                left := left + 1;
                right := right - 1;
            } else {
                // In the original code, only the case currSum == 0 is handled
                // To match the Python code, we do not move left or right otherwise
                // So we break the loop
                break;
            }
        }
        index := index + 1;
    }
    res := resultList;
}

// Helper method to sort a sequence (returns a new sorted sequence)
function method Sort(s: seq<int>): seq<int>
    ensures multiset(s) == multiset(Sort(s))
    ensures forall i, j :: 0 <= i < j < |Sort(s)| ==> Sort(s)[i] <= Sort(s)[j]
{
    if |s| <= 1 then s
    else
        var pivot := s[0];
        var less := [x | x in s[1..], x < pivot];
        var equal := [x | x in s, x == pivot];
        var greater := [x | x in s[1..], x > pivot];
        Sort(less) + equal + Sort(greater)
}