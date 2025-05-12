method LengthOfLongestSubstring(s: seq<char>) returns (res: int)
    ensures 0 <= res <= |s|
    ensures forall i, j :: 0 <= i <= j <= |s| && Unique(s[i..j]) ==> res >= j - i
    ensures exists i, j :: 0 <= i <= j <= |s| && Unique(s[i..j]) && res == j - i
{
    var lastIndex := map[]; // map from char to index +1 (to avoid default 0)
    var start := 0;
    var maxLen := 0;

    var i := 0;
    while i < |s|
        invariant 0 <= start <= i <= |s|
        invariant 0 <= maxLen <= |s|
        invariant forall k, l :: 0 <= k <= l <= i && Unique(s[k..l]) ==> maxLen >= l - k
        invariant forall c :: c in lastIndex ==> 1 <= lastIndex[c] <= i + 1
    {
        if s[i] in lastIndex {
            start := if start > lastIndex[s[i]] then start else lastIndex[s[i]];
        }
        maxLen := if maxLen > i - start + 1 then maxLen else i - start + 1;
        lastIndex := lastIndex[s[i] := i + 1];
        i := i + 1;
    }
    res := maxLen;
}

// Helper predicate: substring is Unique if no character repeats
predicate Unique(a: seq<char>)
{
    forall i, j :: 0 <= i < j < |a| ==> a[i] != a[j]
}