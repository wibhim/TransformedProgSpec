// Dafny Specification and Program for the Zigzag Conversion

method Convert(s: seq<char>, numRows: int) returns (finalString: seq<char>)
    requires numRows >= 1
    ensures numRows == 1 ==> finalString == s
    ensures |finalString| == |s|
    ensures multiset(finalString) == multiset(s)
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
        invariant multiset(ConcatAll(result)) == multiset(s[..idx])
        invariant forall j :: 0 <= j < numRows ==> |result[j]| <= idx
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

    finalString := ConcatAll(result);
}

// Helper function to concatenate all sequences in a sequence of sequences
function method ConcatAll(seqs: seq<seq<char>>): seq<char>
    decreases |seqs|
{
    if |seqs| == 0 then [] else seqs[0] + ConcatAll(seqs[1..])
}