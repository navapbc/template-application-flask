#
# Tests for api.logging.audit.
#

import logging

from api.logging import audit


def test_audit_hook(caplog):
    caplog.set_level(logging.INFO)

    # Should appear in audit log.
    audit.audit_hook("open", ("/dev/null", None, 123000))

    # Various common cases that should not appear in audit log (normal behaviour & too noisy).
    audit.audit_hook("compile", (b"def _(): pass", "<unknown>"))
    audit.audit_hook(
        "open", ("/srv/api/__pycache__/status.cpython-310.pyc", "r", 500010)
    )
    audit.audit_hook("os.chmod", (7, 1, -1))
    audit.audit_hook(
        "open", ("/app/.venv/lib/python3.10/site-packages/pytz/zoneinfo/US/Eastern", "r", 524288)
    )

    assert [(r.funcName, r.levelname, r.message) for r in caplog.records] == [
        ("audit_log", "AUDIT", "open")
    ]
    assert caplog.records[0].__dict__["audit.event_name"] == "open"
    assert caplog.records[0].__dict__["audit.args.0"] == "/dev/null"
    assert caplog.records[0].__dict__["audit.args.1"] is None
    assert caplog.records[0].__dict__["audit.args.2"] == 123000
    assert "audit.args.3" not in caplog.records[0].__dict__


def test_audit_log_repeated_message(caplog):
    caplog.set_level(logging.INFO)

    for _i in range(500):
        audit.audit_log("abc", (1, 2, 3))

    assert [(r.funcName, r.levelname, r.message, r.count) for r in caplog.records] == [
        ("audit_log", "AUDIT", "abc", 1),
        ("audit_log", "AUDIT", "abc", 2),
        ("audit_log", "AUDIT", "abc", 3),
        ("audit_log", "AUDIT", "abc", 4),
        ("audit_log", "AUDIT", "abc", 5),
        ("audit_log", "AUDIT", "abc", 6),
        ("audit_log", "AUDIT", "abc", 7),
        ("audit_log", "AUDIT", "abc", 8),
        ("audit_log", "AUDIT", "abc", 9),
        ("audit_log", "AUDIT", "abc", 10),
        ("audit_log", "AUDIT", "abc", 20),
        ("audit_log", "AUDIT", "abc", 30),
        ("audit_log", "AUDIT", "abc", 40),
        ("audit_log", "AUDIT", "abc", 50),
        ("audit_log", "AUDIT", "abc", 60),
        ("audit_log", "AUDIT", "abc", 70),
        ("audit_log", "AUDIT", "abc", 80),
        ("audit_log", "AUDIT", "abc", 90),
        ("audit_log", "AUDIT", "abc", 100),
        ("audit_log", "AUDIT", "abc", 200),
        ("audit_log", "AUDIT", "abc", 300),
        ("audit_log", "AUDIT", "abc", 400),
        ("audit_log", "AUDIT", "abc", 500),
    ]
