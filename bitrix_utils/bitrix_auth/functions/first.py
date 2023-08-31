def first(iterable):
    try:
        return next(iterable)
    except StopIteration:
        return None
