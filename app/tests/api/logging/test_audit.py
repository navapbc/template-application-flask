#
# Tests for api.logging.audit.
#

import io
import logging
import os
import pathlib
import signal
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
        os.kill,
        (-1, signal.SIGTERM),  # Using PID=-1 since it should not ever be a valid PID
        [
            {
                "msg": "os.kill",
                "audit.args.pid": -1,
                "audit.args.sig": signal.SIGTERM,
            }
        ],
        id="os.kill",
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
        socket.getaddrinfo,
        ("www.python.org", 80),
        [{"msg": "socket.getaddrinfo", "audit.args.host": "www.python.org", "audit.args.port": 80}],
        id="socket.getaddrinfo",
    ),
    pytest.param(
        urllib.request.urlopen,
        ("https://www.python.org",),
        # urllib.request.urlopen calls socket.getaddrinfo and socket.connect under the hood,
        # both of which trigger audit log entries
        [
            {
                "msg": "urllib.Request",
                "audit.args.url": "https://www.python.org",
                "audit.args.method": "GET",
            },
            {
                "msg": "socket.getaddrinfo",
                "audit.args.host": "www.python.org",
                "audit.args.port": 443,
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

    try:
        func(*args)
    except Exception:
        pass

    assert len(caplog.records) == len(expected_records)
    for record, expected_record in zip(caplog.records, expected_records):
        assert record.levelname == "AUDIT"
        assert_record_match(record, expected_record)


def test_repeated_audit_logs(
    init_audit_hook, caplog: pytest.LogCaptureFixture, tmp_path: pathlib.Path
):
    caplog.set_level(logging.INFO)
    caplog.clear()

    for _ in range(1000):
        open(tmp_path / "repeated-audit-logs", "w")

    for r in caplog.records:
        print(r.__dict__["msg"], r.__dict__["count"])

    expected_records = [
        {"msg": "open", "count": 1},
        {"msg": "open", "count": 2},
        {"msg": "open", "count": 3},
        {"msg": "open", "count": 4},
        {"msg": "open", "count": 5},
        {"msg": "open", "count": 6},
        {"msg": "open", "count": 7},
        {"msg": "open", "count": 8},
        {"msg": "open", "count": 9},
        {"msg": "open", "count": 10},
        {"msg": "open", "count": 20},
        {"msg": "open", "count": 30},
        {"msg": "open", "count": 40},
        {"msg": "open", "count": 50},
        {"msg": "open", "count": 60},
        {"msg": "open", "count": 70},
        {"msg": "open", "count": 80},
        {"msg": "open", "count": 90},
        {"msg": "open", "count": 100},
        {"msg": "open", "count": 200},
        {"msg": "open", "count": 300},
        {"msg": "open", "count": 400},
        {"msg": "open", "count": 500},
        {"msg": "open", "count": 600},
        {"msg": "open", "count": 700},
        {"msg": "open", "count": 800},
        {"msg": "open", "count": 900},
        {"msg": "open", "count": 1000},
    ]

    assert len(caplog.records) == len(expected_records)
    for record, expected_record in zip(caplog.records, expected_records):
        assert record.levelname == "AUDIT"
        assert_record_match(record, expected_record)


def assert_record_match(record: logging.LogRecord, expected_record: dict[str, Any]):
    for key, value in expected_record.items():
        assert record.__dict__[key] == value
