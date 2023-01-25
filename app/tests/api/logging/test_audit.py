#
# Tests for api.logging.audit.
#

import re
import io
import logging
import os
import socket
import sys
from typing import Any, Callable

import pytest

import api.logging.audit as audit


@pytest.fixture(scope="session")
def init_audit_hook():
    audit.init()


test_audit_hook_data = [
    pytest.param(eval, ("1+1", None, None), "exec", {}, id="eval"),
    pytest.param(exec, ("1+1", None, None), "exec", {}, id="exec"),
    pytest.param(
        open,
        ("/dev/null", "w"),
        "open",
        {
            "audit.args.path": "/dev/null",
            "audit.args.mode": "w",
            "audit.args.flags": 524865,
        },
        id="open",
    ),
    pytest.param(
        io.open,
        ("/dev/null", "w"),
        "open",
        {
            "audit.args.path": "/dev/null",
            "audit.args.mode": "w",
            "audit.args.flags": 524865,
        },
        id="io.open",
    ),
    pytest.param(
        os.open,
        ("/dev/null", os.O_RDWR | os.O_CREAT, 0o777),
        "open",
        {
            "audit.args.path": "/dev/null",
            "audit.args.mode": None,
            "audit.args.flags": 524354,
        },
        id="os.open",
    ),
    pytest.param(
        sys.addaudithook,
        (lambda *args: None,),
        "sys.addaudithook",
        {},
        id="sys.addaudithook",
    ),
    pytest.param(
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect,
        (("www.python.org", 80),),
        "socket.connect",
        {"audit.args.address": ("www.python.org", 80)},
        id="socket.connect",
    ),
]


@pytest.mark.parametrize("func,args,expected_msg,expected_extra", test_audit_hook_data)
def test_audit_hook(
    init_audit_hook,
    caplog: pytest.LogCaptureFixture,
    func: Callable,
    args: tuple[Any],
    expected_msg: str,
    expected_extra: dict[str, Any],
):
    caplog.set_level(logging.INFO)
    caplog.clear()

    func(*args)
    assert len(caplog.records) == 1
    log_record: logging.LogRecord = caplog.records[0]
    assert log_record.levelname == "AUDIT"
    assert log_record.msg == expected_msg
    for key, value in expected_extra.items():
        assert log_record.__dict__[key] == value
