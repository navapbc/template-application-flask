from flatten_dict import flatten as flatten_dict


def flatten(d: dict):
    return flatten_dict(d, enumerate_types=(list,))


def assert_dict_subset(subdict, superdict):
    """Assert that a dictionary is a subset of another dictionary.

    :param subdict: The dictionary that is expected to be a subset of
                    the other dictionary.
    :param dictionary: The dictionary that is expected to be a superset
    """
    assert set(flatten(subdict).items()) <= set(flatten(superdict).items())
