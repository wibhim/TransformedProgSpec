def encode_rle(input):
    """
    Gets a stream of data and compresses it
    under a Run-Length Encoding.
    :param input: The data to be encoded.
    :return: The encoded string.
    """
    if not input: return ''

    encoded_str = ''
    prev_ch = ''
    count = 1

    for ch in input:

        # Check If the subsequent character does not match
        if ch != prev_ch:
            # Add the count and character
            if prev_ch:
                encoded_str += str(count) + prev_ch
            # Reset the count and set the character
            count = 1
            prev_ch = ch
        else:
            # Otherwise increment the counter
            count += 1
    else:
        return encoded_str + (str(count) + prev_ch)
