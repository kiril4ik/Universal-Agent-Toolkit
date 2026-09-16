"""Keyboard pack selection using only the platform's standard library."""

from contextlib import contextmanager
import os
import re
import shutil
import sys

from .util import ToolkitError, bold, dim, green


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
        raise ToolkitError("keyboard selection needs a terminal; use explicit flags or --yes")
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
            raise ToolkitError("keyboard selection needs a Windows console; use explicit flags or --yes")
        if not console.SetConsoleMode(handle, mode.value | 0x0001 | 0x0004):
            raise ToolkitError("terminal does not support keyboard selection; use explicit flags or --yes")
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


def _clip(line, width):
    """Clip visible text without splitting terminal color sequences."""
    parts = []
    remaining = width
    for part in re.split(r"(\x1b\[[0-9;]*m)", line):
        if part.startswith("\x1b["):
            parts.append(part)
        else:
            parts.append(part[:remaining])
            remaining -= min(remaining, len(part))
    return "".join(parts)


def select_one(title, options, default, read_key, draw):
    """Select one value with arrows and Enter."""
    items = list(options)
    if not items:
        raise ToolkitError(f"{title} has no choices")
    values = [value for value, _description in items]
    if default not in values:
        raise ToolkitError(f"invalid default {default!r} for {title}")
    cursor = values.index(default)
    start = 0
    label_width = max(len(value) for value in values)
    while True:
        width, height = shutil.get_terminal_size((80, 24))
        capacity = max(1, height - 5)
        start = min(start, cursor)
        start = max(start, cursor - capacity + 1)
        visible = range(start, min(len(items), start + capacity))
        rows = []
        for idx in visible:
            value, description = items[idx]
            prefix = "> " if idx == cursor else "  "
            marker = dim("  default") if value == default else ""
            rows.append(f"{prefix}{value:<{label_width}}  {description}{marker}")
        lines = [bold(title),
                 dim("  Up/Down=move  Enter=select  Esc=cancel"),
                 "", *rows, ""]
        draw([_clip(line, max(1, width - 1)) for line in lines])
        key = read_key()
        if key == "enter":
            return values[cursor]
        if key == "escape":
            raise ToolkitError("cancelled")
        if key == "up":
            cursor = max(0, cursor - 1)
        elif key == "down":
            cursor = min(len(items) - 1, cursor + 1)


def select_many(title, options, selected, read_key, draw, require_one=False):
    """Select zero or more values with arrows, Space, and Enter."""
    items = list(options)
    if not items:
        raise ToolkitError(f"{title} has no choices")
    values = [value for value, _label in items]
    selected = set(selected) & set(values)
    initial = set(selected)
    cursor = 0
    start = 0
    warning = ""
    label_width = max((len(label) for _value, label in items), default=0)
    while True:
        width, height = shutil.get_terminal_size((80, 24))
        capacity = max(1, height - 7)
        start = min(start, cursor)
        start = max(start, cursor - capacity + 1)
        visible = range(start, min(len(items), start + capacity))
        rows = []
        for idx in visible:
            value, label = items[idx]
            prefix = ">  " if idx == cursor else "   "
            mark = green("x") if value in selected else " "
            identifier = dim(f"  {value}") if value != label else ""
            rows.append(f"{prefix}[{mark}] {label:<{label_width}}{identifier}")
        lines = [bold(title),
                 dim("  Up/Down=move  Space=toggle  Enter=accept  Esc=cancel"),
                 dim("  a=all  n=none  r=reset"), "", *rows]
        if warning:
            lines.extend(("", warning))
        lines.append("")
        draw([_clip(line, max(1, width - 1)) for line in lines])
        warning = ""
        key = read_key()
        if key == "enter":
            if require_one and not selected:
                warning = "  choose at least one"
            else:
                return selected
        elif key == "escape":
            raise ToolkitError("cancelled")
        elif key == "up" and items:
            cursor = max(0, cursor - 1)
        elif key == "down" and items:
            cursor = min(len(items) - 1, cursor + 1)
        elif key == " " and items:
            selected.symmetric_difference_update({items[cursor][0]})
        elif key == "a":
            selected = set(values)
        elif key == "n":
            selected.clear()
        elif key == "r":
            selected = set(initial)


def choose_one(title, options, default):
    try:
        with keyboard() as read_key:
            return select_one(title, options, default, read_key, _draw)
    except (EOFError, KeyboardInterrupt):
        raise ToolkitError("cancelled") from None


def choose_many(title, options, selected=(), require_one=False):
    try:
        with keyboard() as read_key:
            return select_many(title, options, selected, read_key, _draw, require_one)
    except (EOFError, KeyboardInterrupt):
        raise ToolkitError("cancelled") from None


def select_packs(catalog, recommended, tokens, read_key, draw):
    selected = set(recommended)
    items = list(catalog)
    cursor = 0
    start = 0
    while True:
        width, height = shutil.get_terminal_size((80, 24))
        capacity = max(2, height - 6)
        start = min(start, cursor)
        while True:
            rows = []
            last_category = None
            visible = []
            for idx in range(start, len(items)):
                pack = items[idx]
                new_category = pack.category != last_category
                if len(rows) + 1 + int(new_category) > capacity:
                    break
                if new_category:
                    rows.append(f"  {bold(pack.category.replace('-', ' ').upper())}")
                    last_category = pack.category
                hits = sorted(set(pack.detect) & tokens)
                why = dim("  detected: " + hits[0]) if hits else (
                    dim("  default") if pack.tier == "core" else "")
                mark = green("x") if pack.id in selected else " "
                prefix = ">  " if idx == cursor else "   "
                rows.append(f"{prefix}[{mark}] {pack.title:<34}{why}")
                visible.append(idx)
            if not items or cursor in visible:
                break
            start += 1
        lines = [bold("Select packs to install"),
                 dim("  Up/Down=move  Space=toggle  Enter=accept  Esc=cancel"),
                 dim("  a=all  n=none  r=reset"), "", *rows, ""]
        draw([_clip(line, max(1, width - 1)) for line in lines])
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
