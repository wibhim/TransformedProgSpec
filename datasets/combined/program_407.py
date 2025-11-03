def _valarray(shape, value=np.nan, typecode=None):
    """Return an array of all value."""

    out = np.ones(shape, dtype=bool) * value
    if typecode is not None:
        out = out.astype(typecode)
    if not isinstance(out, np.ndarray):
        out = np.asarray(out)
    return out
