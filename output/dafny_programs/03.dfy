method LengthOfLongestSubstring(s: seq<char>) returns (result: int)
    requires true
    ensures 0 <= result <= |s|
    ensures forall i, j :: 0 <= i <= j < |s| && (j - i + 1) > result ==>
        exists k, l :: i <= k < l <= j && s[k] == s[l]
    ensures exists i, j :: 0 <= i <= j < |s| && (j - i + 1) == result &&
        (forall k, l :: i <= k < l <= j ==> k == l || s[k] != s[l])
{
    var mapSet := map[]; // map from char to int
    var start := 0;
    result := 0;
    var end := 0;
    while end < |s|
        invariant 0 <= start <= end <= |s|
        invariant 0 <= result <= end - start + 1
        invariant forall c: char :: c in mapSet ==> 1 <= mapSet[c] <= end + 1
        invariant forall c: char :: c in mapSet ==> exists k :: 0 <= k < end && s[k] == c && mapSet[c] == k + 1
        invariant forall i, j :: 0 <= i <= j < end && (j - i + 1) > result ==>
            exists k, l :: i <= k < l <= j && s[k] == s[l]
        invariant exists i, j :: 0 <= i <= j < end && (j - i + 1) == result &&
            (forall k, l :: i <= k < l <= j ==> k == l || s[k] != s[l])
    {
        if s[end] in mapSet {
            start := if mapSet[s[end]] > start then mapSet[s[end]] else start;
        }
        result := if result > end - start + 1 then result else end - start + 1;
        mapSet := mapSet[s[end] := end + 1];
        end := end + 1;
    }
}