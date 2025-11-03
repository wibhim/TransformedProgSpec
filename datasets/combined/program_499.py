def _find_noqa(physical_line: str) -> Match[str] | None:
    return defaults.NOQA_INLINE_REGEXP.search(physical_line)
