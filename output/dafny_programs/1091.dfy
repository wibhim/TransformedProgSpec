// Dafny Specification and Program for shortestPathBinaryMatrix

method ShortestPathBinaryMatrix(grid: array2<bool>) returns (res: int)
    requires grid != null && grid.Length > 0 && grid[0].Length > 0
    modifies grid
    ensures
        // If there is a path from (0,0) to (rows-1,cols-1), res is the length of the shortest such path (in steps)
        // Otherwise, res == -1
        (exists path: seq<(int,int)> ::
            path[0] == (0,0) &&
            path[|path|-1] == (grid.Length-1, grid[0].Length-1) &&
            (forall i :: 0 <= i < |path| ==> 0 <= path[i].0 < grid.Length && 0 <= path[i].1 < grid[0].Length) &&
            (forall i :: 0 <= i < |path| ==> !old(grid)[path[i].0, path[i].1]) &&
            (forall i :: 0 <= i < |path|-1 ==>
                ((abs(path[i+1].0 - path[i].0) <= 1) && (abs(path[i+1].1 - path[i].1) <= 1) && (path[i+1] != path[i]))
            ) &&
            |path| == res
        ) || res == -1
{
    var rows := grid.Length;
    var cols := grid[0].Length;

    if grid[0,0] || grid[rows-1,cols-1] {
        res := -1;
        return;
    }

    var queue := new seq<(int,int,int)>();
    var front := 0;
    queue := queue + [(0,0,1)];
    grid[0,0] := true;

    while front < |queue|
        invariant 0 <= front <= |queue|
        invariant forall i :: 0 <= i < |queue| ==> 0 <= queue[i].0 < rows && 0 <= queue[i].1 < cols
        invariant forall i :: 0 <= i < |queue| ==> 1 <= queue[i].2 <= rows*cols
        decreases |queue| - front
    {
        var row := queue[front].0;
        var col := queue[front].1;
        var dist := queue[front].2;
        if row == rows-1 && col == cols-1 {
            res := dist;
            return;
        }
        var dirs := [(-1,-1), (0,-1), (-1,1), (-1,0), (1,0), (1,-1), (0,1), (1,1)];
        foreach d in dirs {
            var n_row := row + d.0;
            var n_col := col + d.1;
            if 0 <= n_row < rows && 0 <= n_col < cols && !grid[n_row, n_col] {
                grid[n_row, n_col] := true;
                queue := queue + [(n_row, n_col, dist+1)];
            }
        }
        front := front + 1;
    }
    res := -1;
}