def clear_lru_caches() -> None:
    """Clear caches holding references to AST nodes."""
    caches_holding_node_references: list[_lru_cache_wrapper[Any]] = [
        class_is_abstract,
        in_for_else_branch,
        infer_all,
        is_overload_stub,
        overridden_method,
        unimplemented_abstract_methods,
        safe_infer,
        _similar_names,
    ]
    for lru in caches_holding_node_references:
        lru.cache_clear()
