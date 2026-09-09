"""Windows user PATH setup; no administrator privileges required."""

import ntpath
import os


def add_to_user_path(directory: str) -> None:
    import winreg

    def contains(value):
        wanted = ntpath.normcase(ntpath.normpath(directory))
        return any(ntpath.normcase(ntpath.normpath(os.path.expandvars(p.strip('"'))))
                   == wanted for p in value.split(";") if p)

    # Read only the user value: persisting the merged process PATH would
    # duplicate system entries and capture temporary shell additions.
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, "Environment", 0,
                            winreg.KEY_READ | winreg.KEY_WRITE) as key:
        try:
            value, kind = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            value, kind = "", winreg.REG_EXPAND_SZ
        if not contains(value):
            value += (";" if value and not value.endswith(";") else "") + directory
            winreg.SetValueEx(key, "Path", 0, kind, value)

    current = os.environ.get("PATH", "")
    if not contains(current):
        os.environ["PATH"] = current + (";" if current else "") + directory
    _notify_environment()


def _notify_environment() -> None:
    import ctypes
    from ctypes import wintypes

    result = ctypes.c_size_t()
    send = ctypes.windll.user32.SendMessageTimeoutW
    send.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM,
                     wintypes.LPCWSTR, wintypes.UINT, wintypes.UINT,
                     ctypes.POINTER(ctypes.c_size_t)]
    send.restype = wintypes.LPARAM
    send(0xFFFF, 0x001A, 0, "Environment", 0x0002, 1000, ctypes.byref(result))
