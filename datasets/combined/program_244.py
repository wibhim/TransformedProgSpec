def object_distance(
    focal_length_of_lens: float, image_distance_from_lens: float
) -> float:
    """
    Doctests:
    >>> from math import isclose
    >>> isclose(object_distance(10,40), -13.333333333333332)
    True

    >>> from math import isclose
    >>> isclose(object_distance(6.2,1.5), 1.9787234042553192)
    True

    >>> object_distance(0, 20)  # doctest: +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    ValueError: Invalid inputs. Enter non zero values with respect
    to the sign convention.
    """

    if image_distance_from_lens == 0 or focal_length_of_lens == 0:
        raise ValueError(
            "Invalid inputs. Enter non zero values with respect to the sign convention."
        )

    object_distance = 1 / ((1 / image_distance_from_lens) - (1 / focal_length_of_lens))
    return object_distance
