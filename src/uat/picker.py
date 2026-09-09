"""Keyboard pack selection using only the platform's standard library."""

from contextlib import contextmanager
import os
import shutil
import sys

from .util import ToolkitError


def windows_key():
    import msvcrt

    key = msvcrt.getwch()
    if key in ("\x00", "\xe0"):
        return {"H": "up", "P": "down"}.get(msvcrt.getwch(), "")
    return _key_name(key)


def _key_name(key):
    if key in ("\x03", "\x04", ""):
        raise ToolkitError("cancelled")
    return {"\r": "enter", "\n": "enter", "\x1b": "escape"}.get(key, key.lower())


def unix_key():
    import select

    fd = sys.stdin.fileno()
    key = os.read(fd, 1).decode("utf-8", errors="replace")
    if key != "\x1b":
        return _key_name(key)
    # Escape alone cancels; consume a complete CSI/SS3 sequence for arrows.
    sequence = ""
    while select.select([fd], [], [], 0.1)[0]:
        char = os.read(fd, 1).decode("ascii", errors="replace")
        sequence += char
        if not char or (len(sequence) > 1 and "@" <= char <= "~"):
            break
        if len(sequence) >= 16:
            break
    if not sequence:
        return "escape"
    return {"[A": "up", "OA": "up", "[B": "down", "OB": "down"}.get(sequence, "")


@contextmanager
def keyboard():
    """Restore console settings even when selection is cancelled."""
    if not sys.stdin.isatty() or not sys.stdout.isatty() or os.environ.get("TERM") == "dumb":
        raise ToolkitError("keyboard selection needs a terminal; use --packs ID ... or --yes")
    if sys.platform == "win32":
        import ctypes
        import msvcrt
        from ctypes import wintypes

        console = ctypes.WinDLL("kernel32", use_last_error=True)
        console.GetConsoleMode.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        console.SetConsoleMode.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        handle = msvcrt.get_osfhandle(sys.stdout.fileno())
        mode = wintypes.DWORD()
        if not console.GetConsoleMode(handle, ctypes.byref(mode)):
            raise ToolkitError("keyboard selection needs a Windows console; use --packs ID ... or --yes")
        if not console.SetConsoleMode(handle, mode.value | 0x0001 | 0x0004):
            raise ToolkitError("terminal does not support keyboard selection; use --packs ID ... or --yes")
        restore = lambda: console.SetConsoleMode(handle, mode.value)
        read_key = windows_key
    else:
        import termios
        import tty

        fd = sys.stdin.fileno()
        previous = termios.tcgetattr(fd)
        tty.setcbreak(fd)
        restore = lambda: termios.tcsetattr(fd, termios.TCSANOW, previous)
        read_key = unix_key
    try:
        sys.stdout.write("\x1b[?1049h\x1b[?25l")
        sys.stdout.flush()
        yield read_key
    finally:
        try:
            sys.stdout.write("\x1b[?25h\x1b[?1049l")
            sys.stdout.flush()
        finally:
            restore()


def _draw(lines):
    sys.stdout.write("\x1b[H\x1b[2J" + "\n".join(lines))
    sys.stdout.flush()


def select_packs(catalog, recommended, tokens, read_key, draw):
    selected = set(recommended)
    items = list(catalog)
    cursor = 0
    while True:
        width, height = shutil.get_terminal_size((80, 24))
        page = max(1, height - 7)
        start = max(0, cursor - page + 1)
        lines = ["Select skills and packs to install",
                 "Up/Down: move  Space: toggle  Enter: accept",
                 "Esc: cancel  a: all  n: none  r: reset", ""]
        for idx in range(start, min(len(items), start + page)):
            pack = items[idx]
            hits = sorted(set(pack.detect) & tokens)
            why = " detected: " + hits[0] if hits else ""
            mark = "x" if pack.id in selected else " "
            focus = ">" if idx == cursor else " "
            lines.append(f"{focus} [{mark}] {pack.title} ({pack.tier}){why}")
        lines += ["", f"{len(selected)} selected; dependencies added on accept"]
        draw([line[:max(1, width - 1)] for line in lines])
        key = read_key()
        if key == "enter":
            return catalog.expand(selected)
        if key == "escape":
            raise ToolkitError("cancelled")
        if key == "up":
            cursor = max(0, cursor - 1)
        elif key == "down":
            cursor = min(max(0, len(items) - 1), cursor + 1)
        elif key == " " and items:
            selected.symmetric_difference_update({items[cursor].id})
        elif key == "a":
            selected = set(catalog.ids)
        elif key == "n":
            selected.clear()
        elif key == "r":
            selected = set(recommended)


def choose_packs(catalog, recommended, detection):
    try:
        with keyboard() as read_key:
            return select_packs(catalog, recommended, detection.tokens, read_key, _draw)
    except (EOFError, KeyboardInterrupt):
        raise ToolkitError("cancelled") from None
