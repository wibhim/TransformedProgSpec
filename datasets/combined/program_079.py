def pressure_conversion(value: float, from_type: str, to_type: str) -> float:

    """

    Conversion between pressure units.

    >>> pressure_conversion(4, "atm", "pascal")

    405300

    >>> pressure_conversion(1, "pascal", "psi")

    0.00014401981999999998

    >>> pressure_conversion(1, "bar", "atm")

    0.986923

    >>> pressure_conversion(3, "kilopascal", "bar")

    0.029999991892499998

    >>> pressure_conversion(2, "megapascal", "psi")

    290.074434314

    >>> pressure_conversion(4, "psi", "torr")

    206.85984

    >>> pressure_conversion(1, "inHg", "atm")

    0.0334211

    >>> pressure_conversion(1, "torr", "psi")

    0.019336718261000002

    >>> pressure_conversion(4, "wrongUnit", "atm")

    Traceback (most recent call last):

        ...

    ValueError: Invalid 'from_type' value: 'wrongUnit'  Supported values are:

    atm, pascal, bar, kilopascal, megapascal, psi, inHg, torr

    """

    if from_type not in PRESSURE_CONVERSION:

        raise ValueError(

            f"Invalid 'from_type' value: {from_type!r}  Supported values are:\n"

            + ", ".join(PRESSURE_CONVERSION)

        )

    if to_type not in PRESSURE_CONVERSION:

        raise ValueError(

            f"Invalid 'to_type' value: {to_type!r}.  Supported values are:\n"

            + ", ".join(PRESSURE_CONVERSION)

        )

    return (

        value

        * PRESSURE_CONVERSION[from_type].from_factor

        * PRESSURE_CONVERSION[to_type].to_factor

    )
