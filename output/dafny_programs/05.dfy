// Dafny Specification and Program for Longest Palindromic Substring

method IsPalindrome(s: seq<char>, i: int, j: int) returns (b: bool)
    ensures b <==> (forall k :: 0 <= k < (j - i + 1) ==> s[i + k] == s[j - k])
{
    var l := i;
    var r := j;
    while l < r
        invariant i <= l <= r <= j
        invariant forall k :: i <= k < l ==> s[k] == s[j - (k - i)]
        invariant forall k :: r < k <= j ==> s[k] == s[j - (k - i)]
    {
        if s[l] != s[r] {
            return false;
        }
        l := l + 1;
        r := r - 1;
    }
    return true;
}

// Returns the longest palindromic substring of s
method LongestPalindrome(s: seq<char>) returns (res: seq<char>)
    requires |s| >= 0
    ensures (exists i, j :: 0 <= i <= j < |s| && res == s[i..j+1] && IsPalindrome(s, i, j))
    ensures forall i, j :: 0 <= i <= j < |s| && IsPalindrome(s, i, j) ==> |s[i..j+1]| <= |res|
{
    var n := |s|;
    if n == 0 {
        return [];
    }
    var start := 0;
    var maxLen := 1;

    // Helper function to expand around center
    function method Expand(s: seq<char>, left: int, right: int): int
        requires 0 <= left < n
        requires 0 <= right < n
        ensures Expand(s, left, right) == (var l := left; var r := right; while l >= 0 && r < n && s[l] == s[r] { l := l - 1; r := r + 1; }; r - l - 1)
    {
        var l := left;
        var r := right;
        while l >= 0 && r < n && s[l] == s[r] {
            l := l - 1;
            r := r + 1;
        }
        r - l - 1
    }

    var i := 0;
    while i < n
        invariant 0 <= i <= n
        invariant 1 <= maxLen <= n
        invariant 0 <= start < n
        invariant start + maxLen <= n
        invariant IsPalindrome(s, start, start + maxLen - 1)
        invariant forall k :: 0 <= k < i ==> forall l, r :: 0 <= l <= r < n && IsPalindrome(s, l, r) && r - l + 1 > maxLen ==> false
    {
        var len1 := Expand(s, i, i);
        var len2 := if i + 1 < n then Expand(s, i, i + 1) else 0;
        var len := if len1 > len2 then len1 else len2;
        if len > maxLen {
            start := i - (len - 1) / 2;
            maxLen := len;
        }
        i := i + 1;
    }
    res := s[start..start+maxLen];
}

// Example usage
method Main()
{
    var s := "babad";
    var res := LongestPalindrome(s);
    print res, "\n";
}