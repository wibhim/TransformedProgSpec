def archimedes_principle(
    fluid_density: float, volume: float, gravity: float = g
) -> float:
    """
    Args:
        fluid_density: density of fluid (kg/m^3)
        volume: volume of object/liquid being displaced by the object (m^3)
        gravity: Acceleration from gravity. Gravitational force on the system,
            The default is Earth Gravity
    returns:
        the buoyant force on an object in Newtons

    >>> archimedes_principle(fluid_density=500, volume=4, gravity=9.8)
    19600.0
    >>> archimedes_principle(fluid_density=997, volume=0.5, gravity=9.8)
    4885.3
    >>> archimedes_principle(fluid_density=997, volume=0.7)
    6844.061035
    >>> archimedes_principle(fluid_density=997, volume=-0.7)
    Traceback (most recent call last):
        ...
    ValueError: Impossible object volume
    >>> archimedes_principle(fluid_density=0, volume=0.7)
    Traceback (most recent call last):
        ...
    ValueError: Impossible fluid density
    >>> archimedes_principle(fluid_density=997, volume=0.7, gravity=0)
    0.0
    >>> archimedes_principle(fluid_density=997, volume=0.7, gravity=-9.8)
    Traceback (most recent call last):
        ...
    ValueError: Impossible gravity
    """

    if fluid_density <= 0:
        raise ValueError("Impossible fluid density")
    if volume <= 0:
        raise ValueError("Impossible object volume")
    if gravity < 0:
        raise ValueError("Impossible gravity")

    return fluid_density * gravity * volume
