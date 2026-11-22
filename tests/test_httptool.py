import pytest

from arena.httptool import HostLockError, send_request


def test_blocks_external_host():
    with pytest.raises(HostLockError):
        send_request("GET", "http://example.com/")


def test_blocks_unregistered_port():
    with pytest.raises(HostLockError):
        send_request("GET", "http://127.0.0.1:65000/")


def test_blocks_lookalike_host():
    with pytest.raises(HostLockError):
        send_request("GET", "http://127.0.0.1.evil.com/")
