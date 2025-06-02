// Dafny Specification and Program for Longest Common Prefix

method LongestCommonPrefix(strs: seq<seq<char>>) returns (prefix: seq<char>)
    requires forall s :: s in strs ==> |s| >= 0
    ensures
        // The result is a prefix of every string in strs
        forall s :: s in strs ==> prefix == s[..|prefix|]
    ensures
        // The result is the longest such prefix
        forall p: seq<char> :: (forall s :: s in strs ==> p == s[..|p|]) ==> |p| <= |prefix|
{
    if |strs| == 0 {
        prefix := [];
        return;
    }

    var minLength := |strs[0]|;
    var i := 1;
    while i < |strs|
        invariant 1 <= |strs| ==> 0 <= i <= |strs|
        invariant minLength == (if i == 0 then |strs[0]| else SeqMin(Seq([|strs[j]| | j := 0 .. i-1])))
    {
        if |strs[i]| < minLength {
            minLength := |strs[i]|;
        }
        i := i + 1;
    }

    var low := 0;
    var high := minLength;
    while low <= high
        invariant 0 <= low <= minLength+1
        invariant 0 <= high <= minLength
        invariant low >= 0 && high >= 0
        decreases high - low + 1
    {
        var mid := (low + high) / 2;
        if PrefixCheck(strs, mid) {
            low := mid + 1;
        } else {
            high := mid - 1;
        }
    }
    prefix := strs[0][..((low + high) / 2)];
}

// Helper function: check if all strings in strs have the same prefix of length 'index'
function PrefixCheck(strs: seq<seq<char>>, index: int): bool
    requires |strs| > 0 && 0 <= index <= |strs[0]|
    requires forall s :: s in strs ==> |s| >= index
{
    var check_prefix := strs[0][..index];
    forall i :: 0 <= i < |strs| ==> strs[i][..index] == check_prefix
}

// Helper function: minimum of a sequence of integers
function SeqMin(s: seq<int>): int
    requires |s| > 0
{
    if |s| == 1 then s[0] else if s[0] < SeqMin(s[1..]) then s[0] else SeqMin(s[1..])
}