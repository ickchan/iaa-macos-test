# ruff: noqa: E402
import sys
from .controllers.log_bridge import LogBridge
log_bridge = LogBridge(None)
log_bridge.install()

import ctypes
import os
import platform
from ctypes import wintypes
from pathlib import Path
from typing import cast

from PySide6.QtCore import Qt, QAbstractNativeEventFilter, QObject, QUrl, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickWindow
from PySide6.QtWidgets import QApplication
from PySide6.QtQuickControls2 import QQuickStyle

from .controllers import AppController

DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_SYSTEMBACKDROP_TYPE = 38

# 常见值：
# 1 = None
# 2 = MainWindow (Mica)
# 3 = TransientWindow (Acrylic-like)
# 4 = TabbedWindow
DWM_SYSTEMBACKDROP_MAINWINDOW = 2

WNDCA_ACCENT_POLICY = 19

ACCENT_DISABLED = 0
ACCENT_ENABLE_BLURBEHIND = 3
ACCENT_ENABLE_ACRYLICBLURBEHIND = 4


class ACCENT_POLICY(ctypes.Structure):
    _fields_ = [
        ("AccentState", ctypes.c_uint),
        ("AccentFlags", ctypes.c_uint),
        ("GradientColor", ctypes.c_uint),
        ("AnimationId", ctypes.c_uint),
    ]


class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
    _fields_ = [
        ("Attrib", ctypes.c_uint),
        ("pvData", ctypes.c_void_p),
        ("cbData", ctypes.c_size_t),
    ]


def is_windows_11() -> bool:
    return sys.getwindowsversion().build >= 22000


def is_windows_10_1803() -> bool:
    return sys.getwindowsversion().build >= 17134


def enable_mica(hwnd: int) -> int:
    dwmapi = ctypes.windll.dwmapi

    value = ctypes.c_int(DWM_SYSTEMBACKDROP_MAINWINDOW)
    return dwmapi.DwmSetWindowAttribute(
        wintypes.HWND(hwnd),
        ctypes.c_uint(DWMWA_SYSTEMBACKDROP_TYPE),
        ctypes.byref(value),
        ctypes.sizeof(value)
    )


def enable_blur(hwnd: int) -> int:
    user32 = ctypes.windll.user32
    set_window_composition = user32.SetWindowCompositionAttribute
    set_window_composition.argtypes = [wintypes.HWND, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
    set_window_composition.restype = ctypes.c_bool

    accent = ACCENT_POLICY(ACCENT_ENABLE_BLURBEHIND, 0, 0, 0)
    data = WINDOWCOMPOSITIONATTRIBDATA(WNDCA_ACCENT_POLICY, ctypes.addressof(accent), ctypes.sizeof(accent))

    return 0 if set_window_composition(wintypes.HWND(hwnd), ctypes.byref(data)) else -1


def enable_acrylic(hwnd: int) -> int:
    user32 = ctypes.windll.user32
    set_window_composition = user32.SetWindowCompositionAttribute
    set_window_composition.argtypes = [wintypes.HWND, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
    set_window_composition.restype = ctypes.c_bool

    accent = ACCENT_POLICY(ACCENT_ENABLE_ACRYLICBLURBEHIND, 0, 0, 0)
    data = WINDOWCOMPOSITIONATTRIBDATA(WNDCA_ACCENT_POLICY, ctypes.addressof(accent), ctypes.sizeof(accent))

    return 0 if set_window_composition(wintypes.HWND(hwnd), ctypes.byref(data)) else -1


def disable_blur(hwnd: int) -> int:
    user32 = ctypes.windll.user32
    set_window_composition = user32.SetWindowCompositionAttribute
    set_window_composition.argtypes = [wintypes.HWND, ctypes.POINTER(WINDOWCOMPOSITIONATTRIBDATA)]
    set_window_composition.restype = ctypes.c_bool

    accent = ACCENT_POLICY(ACCENT_DISABLED, 0, 0, 0)
    data = WINDOWCOMPOSITIONATTRIBDATA(WNDCA_ACCENT_POLICY, ctypes.addressof(accent), ctypes.sizeof(accent))

    return 0 if set_window_composition(wintypes.HWND(hwnd), ctypes.byref(data)) else -1


# ── Frameless window + snap-layout support (Windows only) ────────────────────
#
# Strategy: Qt.FramelessWindowHint removes WS_CAPTION/WS_THICKFRAME; we
# restore the styles needed for resize handles and snap-layout via SetWindowLong,
# then call DwmExtendFrameIntoClientArea to reinstate the DWM drop shadow.
# WM_NCHITTEST drives hit-zones: HTCAPTION (drag), HTMAXBUTTON (snap-layout
# flyout + OS-handled maximize), HTCLIENT for the min/close buttons (so QML
# receives those clicks), and the eight resize-edge codes.

WM_NCHITTEST   = 0x0084
WM_NCCALCSIZE  = 0x0083
WM_NCMOUSEMOVE = 0x00A0
WM_NCMOUSELEAVE = 0x02A2

# WM_NCHITTEST return codes
HTCLIENT      = 1
HTCAPTION     = 2
HTMINBUTTON   = 8
HTMAXBUTTON   = 9
HTLEFT        = 10
HTRIGHT       = 11
HTTOP         = 12
HTTOPLEFT     = 13
HTTOPRIGHT    = 14
HTBOTTOM      = 15
HTBOTTOMLEFT  = 16
HTBOTTOMRIGHT = 17
HTCLOSE       = 20

# SetWindowLong / window-style constants
_GWL_STYLE      = -16
_WS_CAPTION     = 0x00C00000   # required for DWM minimize/maximize animations
_WS_THICKFRAME  = 0x00040000
_WS_MAXIMIZEBOX = 0x00010000
_WS_MINIMIZEBOX = 0x00020000
_WS_SYSMENU     = 0x00080000

# Title-bar geometry matching TitleBar.qml (logical / device-independent px)
_TITLE_BAR_H = 32   # height of custom title bar
_BTN_W       = 46   # width of each window-control button
_RESIZE_EDGE = 4    # resize-handle hit-zone width


class _MSG(ctypes.Structure):
    _fields_ = [
        ("hWnd",    wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam",  wintypes.WPARAM),
        ("lParam",  wintypes.LPARAM),
        ("time",    wintypes.DWORD),
        ("pt",      wintypes.POINT),
    ]


class _RECT(ctypes.Structure):
    _fields_ = [
        ("left",   ctypes.c_long),
        ("top",    ctypes.c_long),
        ("right",  ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class _NCCALCSIZE_PARAMS(ctypes.Structure):
    _fields_ = [
        ("rgrc", _RECT * 3),
        ("lppos", ctypes.c_void_p),
    ]


class _MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth",    ctypes.c_int),
        ("cxRightWidth",   ctypes.c_int),
        ("cyTopHeight",    ctypes.c_int),
        ("cyBottomHeight", ctypes.c_int),
    ]


class _MaxHoverBridge(QObject):
    """Relays WM_NCMOUSEMOVE/WM_NCMOUSELEAVE for the maximize button to QML."""
    hoveredChanged = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self._hovered = False

    def set_hovered(self, value: bool) -> None:
        if self._hovered != value:
            self._hovered = value
            self.hoveredChanged.emit(value)


class WindowEventFilter(QAbstractNativeEventFilter):
    """
    Handles WM_NCHITTEST for a frameless Qt window so that:
      • Resize borders remain functional on all four edges.
      • The maximize button returns HTMAXBUTTON so Windows 11 shows the
        snap-layout flyout on hover and the OS drives maximize/restore on click.
      • The title-bar drag area returns HTCAPTION for native window dragging
        (including OS double-click to toggle maximize).
      • Minimize and close button areas return HTCLIENT so QML handles them
        (hover highlight + click).
      • WM_NCMOUSEMOVE/WM_NCMOUSELEAVE over HTMAXBUTTON are forwarded to
        maxHoverBridge so QML can render a hover highlight.
    Only installed on Windows; completely inert on other platforms.
    """

    def __init__(self, window: QQuickWindow, max_hover_bridge: _MaxHoverBridge) -> None:
        super().__init__()
        self._hwnd = int(window.winId())
        self.maxHoverBridge = max_hover_bridge

    def nativeEventFilter(self, eventType: bytes, message: int) -> tuple[bool, int]:
        if eventType != b"windows_generic_MSG":
            return False, 0
        msg = ctypes.cast(int(message), ctypes.POINTER(_MSG)).contents
        if msg.hWnd != self._hwnd:
            return False, 0
        if msg.message == WM_NCCALCSIZE and msg.wParam:
            # Collapse the NCA to zero so the native title bar is not rendered,
            # while WS_CAPTION remains set (needed for DWM animations).
            # When maximized, Windows expands the window rect by the resize-border
            # size on all sides so the borders go off-screen.  Compensate by
            # shrinking the proposed client rect's top edge so our content starts
            # flush with the screen top instead of being hidden behind it.
            if ctypes.windll.user32.IsZoomed(msg.hWnd):
                p = ctypes.cast(msg.lParam, ctypes.POINTER(_NCCALCSIZE_PARAMS)).contents
                border = ctypes.windll.user32.GetSystemMetrics(33)  # SM_CYSIZEFRAME
                padded = ctypes.windll.user32.GetSystemMetrics(92)  # SM_CXPADDEDBORDER
                p.rgrc[0].top += border + padded
            return True, 0
        if msg.message == WM_NCHITTEST:
            return self._hit_test(msg)
        if msg.message == WM_NCMOUSEMOVE:
            self.maxHoverBridge.set_hovered(msg.wParam == HTMAXBUTTON)
            return False, 0
        if msg.message == WM_NCMOUSELEAVE:
            self.maxHoverBridge.set_hovered(False)
            return False, 0
        return False, 0

    def _hit_test(self, msg: _MSG) -> tuple[bool, int]:
        # lParam carries screen coordinates as two signed 16-bit values.
        sx = ctypes.c_short(msg.lParam & 0xFFFF).value
        sy = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value

        wr = _RECT()
        ctypes.windll.user32.GetWindowRect(msg.hWnd, ctypes.byref(wr))

        # Convert to window-local physical pixels.
        wx = sx - wr.left
        wy = sy - wr.top
        ww = wr.right  - wr.left
        wh = wr.bottom - wr.top

        # Scale logical sizes → physical pixels using the window's DPI.
        dpi    = ctypes.windll.user32.GetDpiForWindow(msg.hWnd)
        scale  = dpi / 96.0
        tb_h   = round(_TITLE_BAR_H * scale)
        btn_w  = round(_BTN_W       * scale)
        border = round(_RESIZE_EDGE * scale)
        is_max = bool(ctypes.windll.user32.IsZoomed(msg.hWnd))

        # ── Resize borders (suppressed when maximized) ────────────────────
        if not is_max:
            top_e    = wy < border
            bottom_e = wy >= wh - border
            left_e   = wx < border
            right_e  = wx >= ww - border
            if top_e    and left_e:  return True, HTTOPLEFT
            if top_e    and right_e: return True, HTTOPRIGHT
            if bottom_e and left_e:  return True, HTBOTTOMLEFT
            if bottom_e and right_e: return True, HTBOTTOMRIGHT
            if top_e:    return True, HTTOP
            if bottom_e: return True, HTBOTTOM
            if left_e:   return True, HTLEFT
            if right_e:  return True, HTRIGHT

        # ── Title-bar strip (top 32 px) ──────────────────────────────────
        if wy < tb_h:
            # Buttons right-to-left: close | maximize | minimize
            if wx >= ww - btn_w:
                return False, 0          # close    → HTCLIENT, QML handles
            if wx >= ww - btn_w * 2:
                return True, HTMAXBUTTON # maximize → OS: snap-layout + toggle
            if wx >= ww - btn_w * 3:
                return False, 0          # minimize → HTCLIENT, QML handles
            return True, HTCAPTION       # remaining strip → drag / dbl-click

        return False, 0


def setup_frameless_window(hwnd: int) -> None:
    """
    After Qt strips WS_THICKFRAME / WS_MAXIMIZEBOX via FramelessWindowHint:
      1. Restore those styles so resize handles and snap-layout work.
      2. Call DwmExtendFrameIntoClientArea to reinstate the DWM drop shadow
         (FramelessWindowHint / WS_POPUP suppresses it by default).
      3. Trigger SWP_FRAMECHANGED so the OS recalculates the non-client area.
    """
    user32 = ctypes.windll.user32
    style  = user32.GetWindowLongW(hwnd, _GWL_STYLE)
    style |= _WS_CAPTION | _WS_THICKFRAME | _WS_MAXIMIZEBOX | _WS_MINIMIZEBOX | _WS_SYSMENU
    user32.SetWindowLongW(hwnd, _GWL_STYLE, style)

    # Extend the DWM frame into the entire client area to reinstate shadow and
    # enable Mica/Acrylic compositing over the full window surface.
    margins = _MARGINS(-1, -1, -1, -1)
    ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(hwnd, ctypes.byref(margins))

    # SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
    user32.SetWindowPos(hwnd, None, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0004 | 0x0020)


def resolve_window_style(style: str) -> str:
    if style in ('mica', 'acrylic', 'blur', 'solid'):
        return style
    if is_windows_11():
        return 'mica'
    return 'solid'


def apply_window_style(hwnd: int, style: str) -> None:
    if platform.system() != 'Windows':
        return
    resolved = resolve_window_style(style)
    if resolved == 'mica':
        enable_mica(hwnd)
    elif resolved == 'acrylic':
        enable_acrylic(hwnd)
    elif resolved == 'blur':
        enable_blur(hwnd)
    elif resolved == 'solid':
        disable_blur(hwnd)


def apply_color_scheme(app: QApplication, color_scheme: str) -> None:
    if color_scheme not in ('auto', 'light', 'dark'):
        return

    style_hints = app.styleHints()
    unset_color_scheme = getattr(style_hints, 'unsetColorScheme', None)
    set_color_scheme = getattr(style_hints, 'setColorScheme', None)
    if not callable(set_color_scheme) and not callable(unset_color_scheme):
        return

    if color_scheme == 'auto':
        if callable(unset_color_scheme):
            unset_color_scheme()
        elif callable(set_color_scheme):
            set_color_scheme(Qt.ColorScheme.Unknown)
    elif color_scheme == 'light':
        if callable(set_color_scheme):
            set_color_scheme(Qt.ColorScheme.Light)
    else:
        if callable(set_color_scheme):
            set_color_scheme(Qt.ColorScheme.Dark)


def apply_theme_color(app: QApplication, color_value: str | None) -> None:
    if not color_value:
        # Clear custom palette override and let Fluent/system palette drive colors.
        app.setPalette(QPalette())
        return

    color = QColor(color_value)
    if not color.isValid():
        return

    palette = QPalette(app.palette())
    palette.setColor(QPalette.ColorRole.Highlight, color)
    accent_role = getattr(QPalette.ColorRole, 'Accent', None)
    if accent_role is not None:
        palette.setColor(accent_role, color)
    app.setPalette(palette)


def main() -> None:
    os.environ.setdefault("QSG_RHI_BACKEND", "opengl")
    QQuickWindow.setDefaultAlphaBuffer(True)

    app = QApplication(sys.argv)
    QQuickStyle.setStyle("FluentWinUI3")

    controller = AppController(log_bridge=log_bridge)
    interface = controller.service.config.shared.interface
    apply_color_scheme(app, interface.color_scheme)

    max_hover_bridge = _MaxHoverBridge() if platform.system() == 'Windows' else None

    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('appController', controller)
    engine.rootContext().setContextProperty('runController', controller.runController)
    engine.rootContext().setContextProperty('settingsController', controller.settingsController)
    engine.rootContext().setContextProperty('preferencesController', controller.preferencesController)
    engine.rootContext().setContextProperty('profileStoreBackend', controller.profileStoreBackend)
    engine.rootContext().setContextProperty('progressBridge', controller.progressBridge)
    engine.rootContext().setContextProperty('logBridge', controller.logBridge)
    engine.rootContext().setContextProperty('scrcpyController', controller.scrcpyController)
    engine.rootContext().setContextProperty('helpController', controller.helpController)
    engine.rootContext().setContextProperty('maxHoverBridge', max_hover_bridge)
    engine.addImageProvider('scrcpy', controller.scrcpyController.image_provider)

    icon_path = Path(controller.service.root) / 'assets' / 'icon_round.ico'
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    qml_path = Path(__file__).resolve().parent / 'qml' / 'MainWindow.qml'
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        raise RuntimeError('Failed to load Qt desktop UI.')
    window = cast(QQuickWindow, engine.rootObjects()[0])
    hwnd = int(window.winId())

    # On Windows: install the event filter first (so WM_NCCALCSIZE is handled
    # immediately), then call setup_custom_titlebar which triggers the initial
    # SWP_FRAMECHANGED → WM_NCCALCSIZE to collapse the native title bar.
    # The reference is kept on `app` to prevent garbage collection.
    if platform.system() == 'Windows':
        setup_frameless_window(hwnd)
        app._win_event_filter = WindowEventFilter(window, max_hover_bridge)
        app.installNativeEventFilter(app._win_event_filter)

    def apply_interface_preferences() -> None:
        interface_conf = controller.service.config.shared.interface
        apply_color_scheme(app, interface_conf.color_scheme)
        apply_theme_color(app, interface_conf.theme_color)
        apply_window_style(hwnd, interface_conf.window_style)
        controller.refreshWindowStyle()

    controller.preferencesController.runtimeChanged.connect(apply_interface_preferences)
    apply_interface_preferences()

    exit_code = app.exec()
    controller.shutdown()
    raise SystemExit(exit_code)
