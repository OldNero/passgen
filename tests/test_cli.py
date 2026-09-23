from passgen.main import load_history, main


def test_cli_default_generation(capsys, tmp_path, monkeypatch):
    history_file = tmp_path / "history.json"
    monkeypatch.setattr("passgen.core.HISTORY_FILE", history_file)
    monkeypatch.setattr("passgen.main.HISTORY_FILE", history_file)

    code = main([])
    assert code == 0

    # Verify saved in history
    history = load_history(history_file)
    assert len(history) == 1
    assert len(history[0]["password"]) == 16  # default length is 16

    # Rich output should contain the password somewhere in the panel
    out = capsys.readouterr().out
    assert history[0]["password"] in out


def test_cli_clear_history(capsys, tmp_path, monkeypatch):
    history_file = tmp_path / "history.json"
    history_file.write_text("[]")
    monkeypatch.setattr("passgen.core.HISTORY_FILE", history_file)
    monkeypatch.setattr("passgen.main.HISTORY_FILE", history_file)

    assert history_file.exists()
    code = main(["--clear-history"])
    assert code == 0
    assert not history_file.exists()
    assert "cleared" in capsys.readouterr().out.lower()


def test_cli_history_display(capsys, tmp_path, monkeypatch):
    history_file = tmp_path / "history.json"
    monkeypatch.setattr("passgen.core.HISTORY_FILE", history_file)
    monkeypatch.setattr("passgen.main.HISTORY_FILE", history_file)

    # Empty history
    code = main(["-H"])
    assert code == 0
    assert "No" in capsys.readouterr().out  # "No password history found."

    # Populated history
    main(["-c", "3", "-m", "my-account"])
    capsys.readouterr()  # discard generation output

    code = main(["-H"])
    assert code == 0
    out = capsys.readouterr().out
    assert "my-account" in out
    assert "3" in out  # 3 entries visible in the table
