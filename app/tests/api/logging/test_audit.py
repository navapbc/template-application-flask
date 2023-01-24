#
# Tests for api.logging.audit.
#

import logging

import api.logging.audit as audit


def test_audit_hook(caplog):
    audit.init()
    caplog.set_level(logging.INFO)

    # Should appear in audit log.
    audit.handle_audit_event("io.open", ("/dev/null", None, 123000))

    # Various common cases that should not appear in audit log (normal behaviour & too noisy).
    audit.handle_audit_event("compile", (b"def _(): pass", "<unknown>"))
    audit.handle_audit_event("open", ("/srv/api/__pycache__/status.cpython-310.pyc", "r", 500010))
    audit.handle_audit_event("os.chmod", (7, 1, -1))
    audit.handle_audit_event(
        "open", ("/app/.venv/lib/python3.10/site-packages/pytz/zoneinfo/US/Eastern", "r", 524288)
    )

    assert [(r.funcName, r.levelname, r.message) for r in caplog.records] == [
        ("log_audit_event", "AUDIT", "io.open")
    ]
    assert caplog.records[0].__dict__["audit.args.path"] == "/dev/null"
    assert caplog.records[0].__dict__["audit.args.mode"] is None
    assert caplog.records[0].__dict__["audit.args.flags"] == 123000
