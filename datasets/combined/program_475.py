def distance(a: Point, b: Point) -> float:
    """
    >>> point1 = Point(2, -1, 7)
    >>> point2 = Point(1, -3, 5)
    >>> print(f"Distance from {point1} to {point2} is {distance(point1, point2)}")
    Distance from Point(2, -1, 7) to Point(1, -3, 5) is 3.0
    """
    return math.sqrt(abs((b.x - a.x) ** 2 + (b.y - a.y) ** 2 + (b.z - a.z) ** 2))
