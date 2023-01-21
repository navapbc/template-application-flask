from api.util.string_utils import blank_for_null, join_list


def test_join_list():
    assert join_list(None) == ""
    assert join_list(None, ",") == ""
    assert join_list(None, "|") == ""
    assert join_list([]) == ""
    assert join_list([], ",") == ""
    assert join_list([], "|") == ""

    assert join_list(["a", "b", "c"]) == "a\nb\nc"
    assert join_list(["a", "b", "c"], ",") == "a,b,c"
    assert join_list(["a", "b", "c"], "|") == "a|b|c"


def test_blank_for_null():
    assert blank_for_null(None) == ""
    assert blank_for_null("hello") == "hello"
    assert blank_for_null(4) == "4"
    assert blank_for_null(["a", "b"]) == "['a', 'b']"
