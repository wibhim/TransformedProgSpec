def get_3d_vectors_cross(ab: Vector3d, ac: Vector3d) -> Vector3d:
    """
    Get the cross of the two vectors AB and AC.

    I used determinant of 2x2 to get the determinant of the 3x3 matrix in the process.

    Read More:
        https://en.wikipedia.org/wiki/Cross_product
        https://en.wikipedia.org/wiki/Determinant

    >>> get_3d_vectors_cross((3, 4, 7), (4, 9, 2))
    (-55, 22, 11)
    >>> get_3d_vectors_cross((1, 1, 1), (1, 1, 1))
    (0, 0, 0)
    >>> get_3d_vectors_cross((-4, 3, 0), (3, -9, -12))
    (-36, -48, 27)
    >>> get_3d_vectors_cross((17.67, 4.7, 6.78), (-9.5, 4.78, -19.33))
    (-123.2594, 277.15110000000004, 129.11260000000001)
    """
    x = ab[1] * ac[2] - ab[2] * ac[1]  # *i
    y = (ab[0] * ac[2] - ab[2] * ac[0]) * -1  # *j
    z = ab[0] * ac[1] - ab[1] * ac[0]  # *k
    return (x, y, z)
