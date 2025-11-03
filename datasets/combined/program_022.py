def _xor_table() -> List[bytes]:
    return [bytes(a ^ b for a in range(256)) for b in range(256)]
