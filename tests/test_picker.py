import base64
from unittest.mock import patch

from passgen.picker import copy_to_clipboard, pick_and_copy


def test_pick_and_copy_empty_returns_none():
    assert pick_and_copy([]) is None


def test_copy_to_clipboard_osc52():
    with patch("sys.stdout.write") as mock_write, patch("sys.stdout.flush"):
        res = copy_to_clipboard("test_secret")
        assert res is True
        b64 = base64.b64encode(b"test_secret").decode("ascii")
        mock_write.assert_called_with(f"\033]52;c;{b64}\a")


def test_copy_to_clipboard_wayland_fallback():
    # Make OSC-52 fail, test wl-copy
    with patch("sys.stdout.write", side_effect=Exception("No OSC-52")), \
         patch("shutil.which", side_effect=lambda cmd: cmd == "wl-copy"), \
         patch("subprocess.run") as mock_run:
        res = copy_to_clipboard("wayland_secret")
        assert res is True
        mock_run.assert_called_once_with(["wl-copy"], input=b"wayland_secret", check=True)


def test_copy_to_clipboard_x11_fallback():
    # Make OSC-52 fail, test xclip
    with patch("sys.stdout.write", side_effect=Exception("No OSC-52")), \
         patch("shutil.which", side_effect=lambda cmd: cmd == "xclip"), \
         patch("subprocess.run") as mock_run:
        res = copy_to_clipboard("x11_secret")
        assert res is True
        mock_run.assert_called_once_with(
            ["xclip", "-selection", "clipboard"], input=b"x11_secret", check=True
        )


def test_copy_to_clipboard_macos_fallback():
    # Make OSC-52 fail, test pbcopy
    with patch("sys.stdout.write", side_effect=Exception("No OSC-52")), \
         patch("shutil.which", side_effect=lambda cmd: cmd == "pbcopy"), \
         patch("subprocess.run") as mock_run:
        res = copy_to_clipboard("macos_secret")
        assert res is True
        mock_run.assert_called_once_with(["pbcopy"], input=b"macos_secret", check=True)
