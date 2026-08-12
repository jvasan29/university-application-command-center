from datetime import date, timedelta
from app import deadline_status, parse_deadline


def test_parse_deadline():
    assert parse_deadline("2030-01-02").isoformat() == "2030-01-02"
    assert parse_deadline("") is None
    assert parse_deadline("bad") is None


def test_deadline_status_near():
    near = (date.today() + timedelta(days=7)).isoformat()
    result = deadline_status(near)
    assert result["days"] == 7
    assert result["class"] == "danger"


def test_deadline_status_far():
    far = (date.today() + timedelta(days=100)).isoformat()
    result = deadline_status(far)
    assert result["days"] == 100
    assert result["class"] == "success"
