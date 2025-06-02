// Dafny Specification and Program for Longest Palindromic Substring

method IsPalindrome(s: seq<char>, i: int, j: int) returns (b: bool)
    ensures b <==> (forall k :: 0 <= k < (j - i + 1) ==> s[i + k] == s[j - k])
{
    var res := true;
    var left := i;
    var right := j;
    while left < right
        invariant i <= left <= right + 1 <= j + 1 <= |s| + 1
        invariant res ==> (forall k :: i <= k < left ==> s[k] == s[j - (k - i)])
        decreases right - left
    {
        if s[left] != s[right] {
            res := false;
            break;
        }
        left := left + 1;
        right := right - 1;
    }
    b := res;
}

// Main method: Returns the longest palindromic substring of s
method LongestPalindrome(s: seq<char>) returns (res: seq<char>)
    requires |s| >= 0
    ensures (exists i, j :: 0 <= i <= j < |s| && res == s[i..j+1] && IsPalindrome(s, i, j))
    ensures (forall i, j :: 0 <= i <= j < |s| && IsPalindrome(s, i, j) ==> |res| >= j - i + 1)
{
    if |s| == 0 {
        res := [];
        return;
    }
    var maxLen := 1;
    var start := 0;

    var i := 0;
    while i < |s|
        invariant 0 <= i <= |s|
        invariant 1 <= maxLen <= |s|
        invariant 0 <= start < |s|
        invariant (forall k :: 0 <= k < i ==> (forall l :: 1 <= l <= maxLen ==> (exists a :: 0 <= a <= k && a + l - 1 < |s| && IsPalindrome(s, a, a + l - 1))))
        decreases |s| - i
    {
        // Odd length palindrome
        var l := i;
        var r := i;
        while l >= 0 && r < |s| && s[l] == s[r]
            invariant 0 <= l + 1 <= i + 1
            invariant i <= r < |s|
            decreases l + 1
        {
            if r - l + 1 > maxLen {
                start := l;
                maxLen := r - l + 1;
            }
            l := l - 1;
            r := r + 1;
        }
        // Even length palindrome
        l := i;
        r := i + 1;
        while l >= 0 && r < |s| && s[l] == s[r]
            invariant 0 <= l + 1 <= i + 1
            invariant i + 1 <= r < |s| + 1
            decreases l + 1
        {
            if r - l + 1 > maxLen {
                start := l;
                maxLen := r - l + 1;
            }
            l := l - 1;
            r := r + 1;
        }
        i := i + 1;
    }
    res := s[start..start+maxLen];
}