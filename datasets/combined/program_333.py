def rotate(vector: np.ndarray, angle_in_degrees: float) -> np.ndarray:
    """
    Standard rotation of a 2D vector with a rotation matrix
    (see https://en.wikipedia.org/wiki/Rotation_matrix )
    >>> rotate(np.array([1, 0]), 60)
    array([0.5      , 0.8660254])
    >>> rotate(np.array([1, 0]), 90)
    array([6.123234e-17, 1.000000e+00])
    """
    theta = np.radians(angle_in_degrees)
    c, s = np.cos(theta), np.sin(theta)
    rotation_matrix = np.array(((c, -s), (s, c)))
    return np.dot(rotation_matrix, vector)
