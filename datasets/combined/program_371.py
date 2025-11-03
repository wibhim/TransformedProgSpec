def object_distance(focal_length: float, distance_of_image: float) -> float:
    """
    >>> from math import isclose
    >>> isclose(object_distance(30, 20), -60.0)
    True
    >>> from math import isclose
    >>> isclose(object_distance(10.5, 11.7), 102.375)
    True
    >>> object_distance(90, 0)  # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    ValueError: Invalid inputs. Enter non zero values with respect
    to the sign convention.
    """

    if distance_of_image == 0 or focal_length == 0:
        raise ValueError(
            "Invalid inputs. Enter non zero values with respect to the sign convention."
        )
    object_distance = 1 / ((1 / focal_length) - (1 / distance_of_image))
    return object_distance
