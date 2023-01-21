import json
import logging
import re

import pytest

import api.logging.formatters as formatters


def test_json_formatter(capsys: pytest.CaptureFixture):
    logger = logging.getLogger("test_json_formatter")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatters.JsonFormatter())
    logger.addHandler(console_handler)

    logger.warning("hello", extra={"foo": "bar"})

    json_record = json.loads(capsys.readouterr().err)
    expected = {
        "name": "test_json_formatter",
        "msg": "hello",
        "levelname": "WARNING",
        "levelno": 30,
        "filename": "test_formatters.py",
        "module": "test_formatters",
        "funcName": "test_json_formatter",
        "foo": "bar",
    }
    assert json_record | expected == json_record


def test_human_readable_formatter(capsys: pytest.CaptureFixture):
    logger = logging.getLogger("test_human_readable_formatter")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatters.HumanReadableFormatter())
    logger.addHandler(console_handler)

    logger.warning("hello", extra={"foo": "bar"})

    text = capsys.readouterr().err
    assert re.match(
        r"\d{2}:\d{2}:\d{2}\.\d{3}  test_human_readable_formatter       \x1b\[0m test_human_readable_formatter \x1b\[31mWARNING  hello                                                                            \x1b\[34mfoo=bar\x1b\[0m\n",
        text,
    )
