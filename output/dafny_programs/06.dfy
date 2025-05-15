// Dafny Specification and Program for Zigzag Conversion

method Convert(s: seq<char>, numRows: int) returns (res: seq<char>)
    requires numRows >= 1
    ensures numRows == 1 ==> res == s
    ensures |res| == |s|
    ensures multiset(res) == multiset(s)
    // The output is the zigzag conversion of s with numRows rows
{
    if numRows == 1 {
        return s;
    }

    var result := new seq<char>[numRows];
    var i := 0;
    while i < numRows
        invariant 0 <= i <= numRows
        invariant |result| == numRows
        invariant forall j :: 0 <= j < i ==> result[j] == []
    {
        result[i] := [];
        i := i + 1;
    }

    var row := 0;
    var down := true;
    var idx := 0;
    while idx < |s|
        invariant 0 <= row < numRows
        invariant 0 <= idx <= |s|
        invariant |result| == numRows
        invariant forall j :: 0 <= j < numRows ==> result[j].Length <= idx
        invariant multiset(SeqConcat(result)) == multiset(s[..idx])
    {
        result[row] := result[row] + [s[idx]];
        if row == numRows - 1 {
            down := false;
        }
        if row == 0 {
            down := true;
        }
        if down {
            row := row + 1;
        } else {
            row := row - 1;
        }
        idx := idx + 1;
    }

    // Concatenate all rows
    var final_string := [];
    var j := 0;
    while j < numRows
        invariant 0 <= j <= numRows
        invariant |final_string| == sum k | 0 <= k < j :: |result[k]|
        invariant multiset(final_string) == multiset(SeqConcat(result[..j]))
    {
        final_string := final_string + result[j];
        j := j + 1;
    }
    res := final_string;
}

// Helper function to concatenate a sequence of sequences
function method SeqConcat(ss: seq<seq<char>>): seq<char>
    decreases |ss|
{
    if |ss| == 0 then [] else ss[0] + SeqConcat(ss[1..])
}