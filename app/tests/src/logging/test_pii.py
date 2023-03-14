import pytest
import logging
import src.logging.pii as pii


@pytest.mark.parametrize(
    "input,expected",
    [
        ("", ""),
        ("1234", "1234"),
        (1234, 1234),
        (None, None),
        ("hostname ip-10-11-12-134.ec2.internal", "hostname ip-10-11-12-134.ec2.internal"),
        ({}, {}),
        ("123456789", "*********"),
        (123456789, "*********"),
        ("123-45-6789", "*********"),
        ("123456789 test", "********* test"),
        ("test 123456789", "test *********"),
        ("test 123456789 test", "test ********* test"),
        ("test=999000000.", "test=*********."),
        ("test=999000000,", "test=*********,"),
        (999000000.5, 999000000.5),
        ({"a": "x", "b": "999000000"}, "{'a': 'x', 'b': '*********'}"),
    ],
)
def test_mask_pii_private_function(input, expected):
    assert pii._mask_pii(input) == expected


@pytest.mark.parametrize(
    "args,extra,expected",
    [
        (
            ("pii",),
            {"foo": "bar", "tin": "123456789", "dashed-ssn": "123-45-6789"},
            {
                "msg": "pii",
                "foo": "bar",
                "tin": "*********",
                "dashed-ssn": "*********",
            },
        ),
        (
            ("%s %s", "text", "123456789"),
            None,
            {
                "msg": "%s %s",
                "message": "text *********",
            },
        ),
    ],
)
def test_mask_pii_in_log_record(
    init_test_logger, caplog: pytest.LogCaptureFixture, args, extra, expected
):
    logger = logging.getLogger(__name__)

    logger.info(*args, extra=extra)

    assert len(caplog.records) == 1
    assert_dict_contains(caplog.records[0].__dict__, expected)
