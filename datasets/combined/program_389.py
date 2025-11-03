def constant_fold_unary_op(op: str, value: ConstantValue) -> int | float | None:
    if op == "-" and isinstance(value, (int, float)):
        return -value
    elif op == "~" and isinstance(value, int):
        return ~value
    elif op == "+" and isinstance(value, (int, float)):
        return value
    return None
