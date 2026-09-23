import string

import pytest

from passgen.main import AMBIGUOUS, build_pool, main


def test_build_pool_default():
    pool = build_pool()
    assert all(c in pool for c in string.ascii_letters)
    assert all(c in pool for c in string.digits)
    assert all(c in pool for c in string.punctuation)


def test_build_pool_no_letters():
    pool = build_pool(no_letters=True)
    assert not any(c in pool for c in string.ascii_letters)
    assert any(c in pool for c in string.digits)
    assert any(c in pool for c in string.punctuation)


def test_build_pool_no_numbers():
    pool = build_pool(no_numbers=True)
    assert any(c in pool for c in string.ascii_letters)
    assert not any(c in pool for c in string.digits)
    assert any(c in pool for c in string.punctuation)


def test_build_pool_no_specials():
    pool = build_pool(no_specials=True)
    assert any(c in pool for c in string.ascii_letters)
    assert any(c in pool for c in string.digits)
    assert not any(c in pool for c in string.punctuation)


def test_build_pool_no_ambiguous():
    pool = build_pool(no_ambiguous=True)
    assert not any(c in pool for c in AMBIGUOUS)


def test_build_pool_all_excluded_raises():
    with pytest.raises(ValueError, match="All character sets are excluded"):
        build_pool(no_letters=True, no_numbers=True, no_specials=True)


def test_cli_generates_correct_length_and_characters(capsys, tmp_path, monkeypatch):
    test_history = tmp_path / "test_history.json"
    monkeypatch.setattr("passgen.core.HISTORY_FILE", test_history)
    monkeypatch.setattr("passgen.main.HISTORY_FILE", test_history)

    exit_code = main(["-l", "28", "-c", "2", "-nn", "-ns"])
    assert exit_code == 0

    # Verify via history file that correct passwords were generated
    from passgen.main import load_history
    history = load_history(test_history)
    assert len(history) == 2
    for record in history:
        pwd = record["password"]
        assert len(pwd) == 28
        assert pwd.isalpha()  # only letters should be present
