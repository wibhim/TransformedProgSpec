def volume_of_gas_system(moles: float, kelvin: float, pressure: float) -> float:
    """
    >>> volume_of_gas_system(2, 100, 5)
    332.57848
    >>> volume_of_gas_system(0.5, 273, 0.004)
    283731.01575
    >>> volume_of_gas_system(3, -0.46, 23.5)
    Traceback (most recent call last):
        ...
    ValueError: Invalid inputs. Enter positive value.
    """
    if moles < 0 or kelvin < 0 or pressure < 0:
        raise ValueError("Invalid inputs. Enter positive value.")
    return moles * kelvin * UNIVERSAL_GAS_CONSTANT / pressure
