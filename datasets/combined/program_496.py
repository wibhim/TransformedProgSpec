def logprob_specify_shape(op, values, inner_rv, *shapes, **kwargs):
    (value,) = values
    # transfer specify_shape from rv to value
    value = pt.specify_shape(value, shapes)
    return _logprob_helper(inner_rv, value)
