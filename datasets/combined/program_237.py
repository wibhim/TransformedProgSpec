def _integ(img, r, c, rl, cl):
    """Integrate over the 2D integral image in the given window.

    This method was created so that `hessian_det_appx` does not have to make
    a Python call.

    Parameters
    ----------
    img : array
        The integral image over which to integrate.
    r : int
        The row number of the top left corner.
    c : int
        The column number of the top left corner.
    rl : int
        The number of rows over which to integrate.
    cl : int
        The number of columns over which to integrate.

    Returns
    -------
    ans : int
        The integral over the given window.
    """

    r = _clip(r, 0, img.shape[0] - 1)
    c = _clip(c, 0, img.shape[1] - 1)

    r2 = _clip(r + rl, 0, img.shape[0] - 1)
    c2 = _clip(c + cl, 0, img.shape[1] - 1)

    ans = img[r, c] + img[r2, c2] - img[r, c2] - img[r2, c]
    return max(0.0, ans)
