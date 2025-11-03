def warp(
    image: np.ndarray, horizontal_flow: np.ndarray, vertical_flow: np.ndarray
) -> np.ndarray:
    """
    Warps the pixels of an image into a new image using the horizontal and vertical
    flows.
    Pixels that are warped from an invalid location are set to 0.

    Parameters:
        image: Grayscale image
        horizontal_flow: Horizontal flow
        vertical_flow: Vertical flow

    Returns: Warped image

    >>> warp(np.array([[0, 1, 2], [0, 3, 0], [2, 2, 2]]), \
    np.array([[0, 1, -1], [-1, 0, 0], [1, 1, 1]]), \
    np.array([[0, 0, 0], [0, 1, 0], [0, 0, 1]]))
    array([[0, 0, 0],
           [3, 1, 0],
           [0, 2, 3]])
    """
    flow = np.stack((horizontal_flow, vertical_flow), 2)

    # Create a grid of all pixel coordinates and subtract the flow to get the
    # target pixels coordinates
    grid = np.stack(
        np.meshgrid(np.arange(0, image.shape[1]), np.arange(0, image.shape[0])), 2
    )
    grid = np.round(grid - flow).astype(np.int32)

    # Find the locations outside of the original image
    invalid = (grid < 0) | (grid >= np.array([image.shape[1], image.shape[0]]))
    grid[invalid] = 0

    warped = image[grid[:, :, 1], grid[:, :, 0]]

    # Set pixels at invalid locations to 0
    warped[invalid[:, :, 0] | invalid[:, :, 1]] = 0

    return warped
