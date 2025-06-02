// Dafny Specification and Program for shortestPathBinaryMatrix

method ShortestPathBinaryMatrix(grid: array2<bool>) returns (dist: int)
    requires grid != null && grid.Length > 0 && grid[0].Length > 0
    ensures dist == -1 || (dist > 0 && dist <= grid.Length * grid[0].Length)
    ensures dist == -1 ==> !exists path :: IsValidPath(grid, path)
    ensures dist > 0 ==> exists path :: IsValidPath(grid, path) && |path| == dist
{
    var rows := grid.Length;
    var cols := grid[0].Length;

    if grid[0][0] || grid[rows - 1][cols - 1] {
        return -1;
    }

    var visited := new bool[rows, cols];
    visited[0, 0] := true;

    var queue := new seq<(int, int, int)>;
    queue := queue + [(0, 0, 1)];

    var head := 0;
    while head < |queue|
        invariant 0 <= head <= |queue|
        invariant forall i :: 0 <= i < head ==> visited[queue[i].0, queue[i].1]
        invariant forall i :: head <= i < |queue| ==> !visited[queue[i].0, queue[i].1]
    {
        var (row, col, d) := queue[head];
        head := head + 1;

        if row == rows - 1 && col == cols - 1 {
            return d;
        }

        var dirs := [(-1, -1), (0, -1), (-1, 1), (-1, 0), (1, 0), (1, -1), (0, 1), (1, 1)];
        var k := 0;
        while k < |dirs|
            invariant 0 <= k <= |dirs|
        {
            var di := dirs[k].0;
            var dj := dirs[k].1;
            var n_row := row + di;
            var n_col := col + dj;
            if 0 <= n_row < rows && 0 <= n_col < cols && !grid[n_row][n_col] && !visited[n_row, n_col] {
                visited[n_row, n_col] := true;
                queue := queue + [(n_row, n_col, d + 1)];
            }
            k := k + 1;
        }
    }
    return -1;
}

// Helper predicate to define a valid path from (0,0) to (rows-1,cols-1)
predicate IsValidPath(grid: array2<bool>, path: seq<(int, int)>)
    requires grid != null && grid.Length > 0 && grid[0].Length > 0
{
    |path| > 0 &&
    path[0] == (0, 0) &&
    path[|path|-1] == (grid.Length-1, grid[0].Length-1) &&
    forall i :: 0 <= i < |path| ==> 0 <= path[i].0 < grid.Length && 0 <= path[i].1 < grid[0].Length && !grid[path[i].0][path[i].1] &&
    forall i :: 0 <= i < |path|-1 ==> IsNeighbor(path[i], path[i+1])
}

// Helper predicate to define 8-directional adjacency
predicate IsNeighbor(a: (int, int), b: (int, int))
{
    var dr := if a.0 > b.0 then a.0 - b.0 else b.0 - a.0;
    var dc := if a.1 > b.1 then a.1 - b.1 else b.1 - a.1;
    dr <= 1 && dc <= 1 && (dr != 0 || dc != 0)
}