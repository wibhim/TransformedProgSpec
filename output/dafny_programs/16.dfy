// Dafny Specification and Program for threeSumClosest

method threeSumClosest(nums: seq<int>, target: int) returns (result: int)
    requires |nums| >= 3
    ensures exists i, j, k :: 0 <= i < j < k < |nums| && result == nums[i] + nums[j] + nums[k]
    ensures forall i, j, k :: 0 <= i < j < k < |nums| ==>
        abs(target - result) <= abs(target - (nums[i] + nums[j] + nums[k]))
{
    var a := nums[..];
    a := Sort(a);

    var min_diff := int.Max;
    var found := false;
    var best := 0;

    var n := |a|;

    var i := 0;
    while i < n - 2
        invariant 0 <= i <= n - 2
        invariant found ==> exists ii, jj, kk :: 0 <= ii < jj < kk < n && best == a[ii] + a[jj] + a[kk]
        invariant forall ii, jj, kk :: 0 <= ii < jj < kk < n && ii < i ==> abs(target - best) <= abs(target - (a[ii] + a[jj] + a[kk]))
    {
        var left := i + 1;
        var right := n - 1;
        while left < right
            invariant i + 1 <= left <= right + 1 <= n
            invariant found ==> exists ii, jj, kk :: 0 <= ii < jj < kk < n && best == a[ii] + a[jj] + a[kk]
            invariant forall ii, jj, kk :: 0 <= ii < jj < kk < n && (ii < i || (ii == i && (jj < left || kk > right))) ==> abs(target - best) <= abs(target - (a[ii] + a[jj] + a[kk]))
        {
            var currSum := a[i] + a[left] + a[right];
            var diff := if target - currSum >= 0 then target - currSum else currSum - target;
            if diff == 0 {
                result := target;
                return;
            }
            if diff < min_diff {
                min_diff := diff;
                best := currSum;
                found := true;
            }
            if currSum < target {
                left := left + 1;
            } else {
                right := right - 1;
            }
        }
        i := i + 1;
    }
    result := best;
}

// Helper: Stable sort for sequences
function method Sort(s: seq<int>): seq<int>
    ensures multiset(Sort(s)) == multiset(s)
    ensures forall i, j :: 0 <= i < j < |Sort(s)| ==> Sort(s)[i] <= Sort(s)[j]
{
    if |s| <= 1 then s
    else
        var pivot := s[0];
        Sort([x | x <- s[1..], x < pivot]) +
        [pivot] +
        Sort([x | x <- s[1..], x >= pivot])
}

// Helper: Absolute value
function method abs(x: int): int
    ensures abs(x) >= 0
    ensures abs(x) == x || abs(x) == -x
{
    if x >= 0 then x else -x
}