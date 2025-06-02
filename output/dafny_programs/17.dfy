// Dafny Specification and Program for letterCombinations

// Helper function: Map from digit character to string of letters
function method PhoneMap(d: char): seq<char>
    requires d in {'2','3','4','5','6','7','8','9'}
    decreases d
{
    if d == '2' then ['a','b','c']
    else if d == '3' then ['d','e','f']
    else if d == '4' then ['g','h','i']
    else if d == '5' then ['j','k','l']
    else if d == '6' then ['m','n','o']
    else if d == '7' then ['p','q','r','s']
    else if d == '8' then ['t','u','v']
    else ['w','x','y','z']
}

// Specification: For a given sequence of digits (as chars), return all possible letter combinations
// Precondition: All characters in digits are in {'2','3','4','5','6','7','8','9'}
// Postcondition: The result contains all possible combinations (as strings) where each character
//                is chosen from the corresponding digit's mapping in PhoneMap.

method letterCombinations(digits: seq<char>) returns (result: seq<seq<char>>)
    requires forall d :: d in digits ==> d in {'2','3','4','5','6','7','8','9'}
    ensures (|digits| == 0 ==> |result| == 0)
    ensures (|digits| > 0 ==> |result| == ProductLen(digits))
    ensures forall s :: s in result ==> |s| == |digits| &&
        forall i :: 0 <= i < |digits| ==> s[i] in PhoneMap(digits[i])
{
    if |digits| == 0 {
        result := [];
        return;
    }
    var res: seq<seq<char>> := [ [] ];
    var i := 0;
    while i < |digits|
        invariant 0 <= i <= |digits|
        invariant forall s :: s in res ==> |s| == i
        invariant forall s :: s in res ==> forall j :: 0 <= j < i ==> s[j] in PhoneMap(digits[j])
        decreases |digits| - i
    {
        var letters := PhoneMap(digits[i]);
        var newRes: seq<seq<char>> := [];
        var j := 0;
        while j < |res|
            invariant 0 <= j <= |res|
            decreases |res| - j
        {
            var prefix := res[j];
            var k := 0;
            while k < |letters|
                invariant 0 <= k <= |letters|
                decreases |letters| - k
            {
                newRes := newRes + [prefix + [letters[k]]];
                k := k + 1;
            }
            j := j + 1;
        }
        res := newRes;
        i := i + 1;
    }
    result := res;
}

// Helper function to compute the expected number of combinations
function ProductLen(digits: seq<char>): nat
    decreases digits
{
    if |digits| == 0 then 0
    else if |digits| == 1 then |PhoneMap(digits[0])|
    else |PhoneMap(digits[0])| * ProductLen(digits[1..])
}