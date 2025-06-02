method maxArea(height: array<int>) returns (maxArea: int)
    requires height != null && height.Length >= 2
    ensures 0 <= maxArea
    ensures forall i, j :: 0 <= i < j < height.Length ==>
        maxArea >= (if height[i] < height[j] then height[i] else height[j]) * (j - i)
    ensures exists i, j :: 0 <= i < j < height.Length &&
        maxArea == (if height[i] < height[j] then height[i] else height[j]) * (j - i)
{
    var left := 0;
    var right := height.Length - 1;
    maxArea := 0;

    while left < right
        invariant 0 <= left <= right < height.Length
        invariant 0 <= maxArea
        invariant forall i, j :: 0 <= i < j < height.Length && (i < left || j > right) ==>
            maxArea >= (if height[i] < height[j] then height[i] else height[j]) * (j - i)
    {
        var h := if height[left] < height[right] then height[left] else height[right];
        var area := h * (right - left);
        if area > maxArea {
            maxArea := area;
        }
        if height[left] < height[right] {
            left := left + 1;
        } else {
            right := right - 1;
        }
    }
}