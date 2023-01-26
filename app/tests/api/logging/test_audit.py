#
# Tests for api.logging.audit.
#

import io
import logging
import os
import socket
import sys
import urllib.request
from typing import Any, Callable

import pytest

import api.logging.audit as audit


@pytest.fixture(scope="session")
def init_audit_hook():
    audit.init()


test_audit_hook_data = [
    pytest.param(eval, ("1+1", None, None), [{"msg": "exec"}], id="eval"),
    pytest.param(exec, ("1+1", None, None), [{"msg": "exec"}], id="exec"),
    pytest.param(
        open,
        ("/dev/null", "w"),
        [
            {
                "msg": "open",
                "audit.args.path": "/dev/null",
                "audit.args.mode": "w",
                "audit.args.flags": 524865,
            }
        ],
        id="open",
    ),
    pytest.param(
        io.open,
        ("/dev/null", "w"),
        [
            {
                "msg": "open",
                "audit.args.path": "/dev/null",
                "audit.args.mode": "w",
                "audit.args.flags": 524865,
            }
        ],
        id="io.open",
    ),
    pytest.param(
        os.open,
        ("/dev/null", os.O_RDWR | os.O_CREAT, 0o777),
        [
            {
                "msg": "open",
                "audit.args.path": "/dev/null",
                "audit.args.mode": None,
                "audit.args.flags": 524354,
            }
        ],
        id="os.open",
    ),
    pytest.param(
        sys.addaudithook,
        (lambda *args: None,),
        [{"msg": "sys.addaudithook"}],
        id="sys.addaudithook",
    ),
    pytest.param(
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect,
        (("www.python.org", 80),),
        [{"msg": "socket.connect", "audit.args.address": ("www.python.org", 80)}],
        id="socket.connect",
    ),
    pytest.param(
        urllib.request.urlopen,
        ("https://www.python.org",),
        # urllib.request.urlopen calls socket.connect under the hood, which
        # triggers another audit log entry
        [
            {
                "msg": "urllib.Request",
                "audit.args.url": "https://www.python.org",
                "audit.args.method": "GET",
            },
            {
                "msg": "socket.connect",
            },
        ],
        id="urllib.request.urlopen",
    ),
]


@pytest.mark.parametrize("func,args,expected_records", test_audit_hook_data)
def test_audit_hook(
    init_audit_hook,
    caplog: pytest.LogCaptureFixture,
    func: Callable,
    args: tuple[Any],
    expected_records: list[dict[str, Any]],
):
    caplog.set_level(logging.INFO)
    caplog.clear()

    func(*args)

    assert len(caplog.records) == len(expected_records)
    for record, expected_record in zip(caplog.records, expected_records):
        assert record.levelname == "AUDIT"
        for key, value in expected_record.items():
            assert record.__dict__[key] == value
