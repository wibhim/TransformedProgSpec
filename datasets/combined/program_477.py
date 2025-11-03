def retroactive_resolution(
    coefficients: NDArray[float64], vector: NDArray[float64]
) -> NDArray[float64]:
    """
    This function performs a retroactive linear system resolution
    for triangular matrix

    Examples:
        1.
            * 2x1 + 2x2 - 1x3 = 5
            * 0x1 - 2x2 - 1x3 = -7
            * 0x1 + 0x2 + 5x3 = 15
        2.
            * 2x1 + 2x2 = -1
            * 0x1 - 2x2 = -1

    >>> gaussian_elimination([[2, 2, -1], [0, -2, -1], [0, 0, 5]], [[5], [-7], [15]])
    array([[2.],
           [2.],
           [3.]])
    >>> gaussian_elimination([[2, 2], [0, -2]], [[-1], [-1]])
    array([[-1. ],
           [ 0.5]])
    """

    rows, columns = np.shape(coefficients)

    x: NDArray[float64] = np.zeros((rows, 1), dtype=float)
    for row in reversed(range(rows)):
        total = np.dot(coefficients[row, row + 1 :], x[row + 1 :])
        x[row, 0] = (vector[row][0] - total[0]) / coefficients[row, row]

    return x
