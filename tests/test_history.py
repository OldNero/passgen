import json
import os
import time

from passgen.main import (
    MAX_HISTORY,
    format_time_ago,
    load_history,
    save_to_history,
)


def test_format_time_ago():
    now = time.time()
    assert format_time_ago(0) == "unknown"
    assert format_time_ago(now - 30) == "less than a minute ago"
    assert format_time_ago(now - 90) == "1 minute ago"
    assert format_time_ago(now - 300) == "5 minutes ago"
    assert format_time_ago(now - 4000) == "1 hour ago"
    assert format_time_ago(now - 10000) == "2 hours ago"
    assert format_time_ago(now - 90000) == "yesterday"
    assert format_time_ago(now - 200000) == "2 days ago"


def test_load_history_non_existent(tmp_path):
    missing_file = tmp_path / "does_not_exist.json"
    assert load_history(missing_file) == []


def test_load_history_corrupted_json(tmp_path):
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{not: valid, json")
    assert load_history(corrupt_file) == []


def test_load_history_legacy_strings(tmp_path):
    legacy_file = tmp_path / "legacy.json"
    legacy_file.write_text(json.dumps(["old_pwd1", "old_pwd2"]))
    loaded = load_history(legacy_file)
    assert len(loaded) == 2
    assert loaded[0] == {"password": "old_pwd1", "timestamp": 0, "comment": "-"}
    assert loaded[1] == {"password": "old_pwd2", "timestamp": 0, "comment": "-"}


def test_save_to_history_capping_and_permissions(tmp_path):
    history_file = tmp_path / "history.json"

    # Create 30 records (exceeding MAX_HISTORY = 25)
    records = [
        {"password": f"pwd_{i}", "timestamp": time.time(), "comment": f"comm_{i}"}
        for i in range(30)
    ]
    save_to_history(records, file_path=history_file)

    loaded = load_history(history_file)
    assert len(loaded) == MAX_HISTORY
    # Ensure it kept the most recent records (records 5 to 29)
    assert loaded[0]["password"] == "pwd_5"
    assert loaded[-1]["password"] == "pwd_29"

    # Verify 0o600 file permissions (owner read/write only)
    file_stat = os.stat(history_file)
    assert (file_stat.st_mode & 0o777) == 0o600
