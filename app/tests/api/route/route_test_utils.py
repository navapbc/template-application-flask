import flatdict


def assert_dict_subset(subdict, superdict):
    """Assert that a dictionary is a subset of another dictionary.

    :param subdict: The dictionary that is expected to be a subset of
                    the other dictionary.
    :param dictionary: The dictionary that is expected to be a superset
    """
    assert set(flatten(subdict).items()) <= set(flatten(superdict).items())


def flatten(d: dict) -> flatdict.FlatterDict:
    return flatdict.FlatterDict(d, delimiter=".")
