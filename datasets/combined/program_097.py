def _extract_argument_name(expr: Expression) -> str | None:
    if isinstance(expr, NameExpr) and expr.name == "None":
        return None
    elif isinstance(expr, StrExpr):
        return expr.value
    else:
        raise TypeTranslationError()
