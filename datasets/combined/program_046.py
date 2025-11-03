def timeout(seconds: Optional[float]) -> ContextManager[None]:
    """**(Provisional)** Apply the given timeout for a block of operations.

    .. note:: :func:`~pymongo.timeout` is currently provisional. Backwards
       incompatible changes may occur before becoming officially supported.

    Use :func:`~pymongo.timeout` in a with-statement::

      with pymongo.timeout(5):
          client.db.coll.insert_one({})
          client.db.coll2.insert_one({})

    When the with-statement is entered, a deadline is set for the entire
    block. When that deadline is exceeded, any blocking pymongo operation
    will raise a timeout exception. For example::

      try:
          with pymongo.timeout(5):
              client.db.coll.insert_one({})
              time.sleep(5)
              # The deadline has now expired, the next operation will raise
              # a timeout exception.
              client.db.coll2.insert_one({})
      except PyMongoError as exc:
          if exc.timeout:
              print(f"block timed out: {exc!r}")
          else:
              print(f"failed with non-timeout error: {exc!r}")

    When nesting :func:`~pymongo.timeout`, the nested deadline is capped by
    the outer deadline. The deadline can only be shortened, not extended.
    When exiting the block, the previous deadline is restored::

      with pymongo.timeout(5):
          coll.find_one()  # Uses the 5 second deadline.
          with pymongo.timeout(3):
              coll.find_one() # Uses the 3 second deadline.
          coll.find_one()  # Uses the original 5 second deadline.
          with pymongo.timeout(10):
              coll.find_one()  # Still uses the original 5 second deadline.
          coll.find_one()  # Uses the original 5 second deadline.

    :param seconds: A non-negative floating point number expressing seconds, or None.

    :raises: :py:class:`ValueError`: When `seconds` is negative.

    See :ref:`timeout-example` for more examples.

    .. versionadded:: 4.2
    """
    if not isinstance(seconds, (int, float, type(None))):
        raise TypeError(f"timeout must be None, an int, or a float, not {type(seconds)}")
    if seconds and seconds < 0:
        raise ValueError("timeout cannot be negative")
    if seconds is not None:
        seconds = float(seconds)
    return _csot._TimeoutContext(seconds)
