def change_contrast(img: Image, level: int) -> Image:

    """

    Function to change contrast

    """

    factor = (259 * (level + 255)) / (255 * (259 - level))

    def contrast(c: int) -> int:

        """

        Fundamental Transformation/Operation that'll be performed on

        every bit.

        """

        return int(128 + factor * (c - 128))

    return img.point(contrast)
