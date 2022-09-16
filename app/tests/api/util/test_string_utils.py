from api.util.string_utils import blank_for_null, join_list, mask_pii, mask_pii_for_key


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


def test_mask_pii():
    # Scenarios that won't be masked
    assert mask_pii("") == ""
    assert mask_pii("1234") == "1234"
    assert mask_pii(1234) == "1234"
    assert mask_pii(None) == "None"
    assert (
        mask_pii("hostname ip-10-11-12-134.ec2.internal") == "hostname ip-10-11-12-134.ec2.internal"
    )
    assert mask_pii({}) == "{}"

    # Scenarios that will be masked
    assert mask_pii("123456789") == "*********"
    assert mask_pii(123456789) == "*********"
    assert mask_pii("123-45-6789") == "*********"
    assert mask_pii("123456789 test") == "********* test"
    assert mask_pii("test 123456789") == "test *********"
    assert mask_pii("test 123456789 test") == "test ********* test"
    assert mask_pii("test=999000000.") == "test=*********."
    assert mask_pii("test=999000000,") == "test=*********,"
    assert mask_pii(999000000.5) == "999000000.5"
    assert mask_pii({"a": "x", "b": "999000000"}) == "{'a': 'x', 'b': '*********'}"


def test_mask_pii_for_key():
    # Still not allowed as they aren't allowed keys
    assert mask_pii_for_key("message", "123456789") == "*********"
    assert mask_pii_for_key("user_id", 123456789) == "*********"

    # Allowed as we can safely assume they're not PII
    assert mask_pii_for_key("created", "123456789") == "123456789"
    assert mask_pii_for_key("count", 123456789) == "123456789"
