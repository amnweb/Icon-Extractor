import logging
import sys
from app.core.app_icons import get_window_icon
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QGraphicsOpacityEffect
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6 import QtCore
import psutil
import ctypes
import win32gui
from PyQt6.QtCore import QTimer, pyqtSignal, QObject, QCoreApplication
import threading
from PIL import Image
import os

IGNORED_TITLES = ['', ' ', 'FolderView', 'Program Manager', 'python3', 'pythonw3', 'YasbBar', 'Search', 'Start','Windows Shell Experience Host']

class EventListener(QObject):
    focused_window_changed = pyqtSignal(str, int)

    def __init__(self, own_pid):
        super().__init__()
        self.own_pid = own_pid  # Store the application's PID
        self.user32 = ctypes.windll.user32
        self.WINEVENT_OUTOFCONTEXT = 0x0000
        self.EVENT_SYSTEM_FOREGROUND = 0x0003
        self.EVENT_OBJECT_LOCATIONCHANGE = 0x800B
        self.WinEventProcType = ctypes.WINFUNCTYPE(
            None, ctypes.wintypes.HANDLE, ctypes.wintypes.DWORD,
            ctypes.wintypes.HWND, ctypes.wintypes.LONG,
            ctypes.wintypes.LONG, ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD)
        self.WinEventProc = self.WinEventProcType(self.callback)

    def callback(self, hWinEventHook, event, hwnd, idObject, idChild, dwEventThread, dwmsEventTime):
        process_name, hwnd = get_active_window_process()
        if process_name:
            try:
                # Get the process ID of the foreground window
                pid = self.get_window_pid(hwnd)
                if pid and pid != self.own_pid:
                    self.focused_window_changed.emit(process_name, hwnd)
            except Exception:
                logging.exception(f"Failed to get process ID for HWND {hwnd}")

    def get_window_pid(self, hwnd):
        pid = ctypes.c_ulong()
        result = self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if result:
            return pid.value
        return None

    def hook(self):
        self.user32.SetWinEventHook.argtypes = [
            ctypes.wintypes.DWORD, ctypes.wintypes.DWORD,
            ctypes.wintypes.HMODULE, self.WinEventProcType,
            ctypes.wintypes.DWORD, ctypes.wintypes.DWORD,
            ctypes.wintypes.DWORD]
        self.user32.SetWinEventHook.restype = ctypes.wintypes.HANDLE
        self.hooked = self.user32.SetWinEventHook(
            self.EVENT_SYSTEM_FOREGROUND,
            self.EVENT_OBJECT_LOCATIONCHANGE,
            0,
            self.WinEventProc,
            0,
            0,
            self.WINEVENT_OUTOFCONTEXT)
        msg = ctypes.wintypes.MSG()
        while self.user32.GetMessageA(ctypes.byref(msg), 0, 0, 0) != 0:
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageA(ctypes.byref(msg))

def get_active_window_process():
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    pid = ctypes.c_ulong()
    # Use ctypes to call GetWindowThreadProcessId instead of win32gui
    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    try:
        process = psutil.Process(pid.value)
        return process.name(), hwnd
    except psutil.NoSuchProcess:
        return None, None

def main():
    app = QtWidgets.QApplication([])
    app.setStyle("Fusion")
    window = QtWidgets.QWidget()
    window.setWindowFlags(window.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
    window.setWindowTitle("Icon Extractor")
    window.setWindowIcon(QIcon('app/assets/icon.ico'))
 
    window.resize(500, 500)
    layout = QVBoxLayout()
    layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    placeholder_label = QLabel()
    opacity_effect = QGraphicsOpacityEffect()
    opacity_effect.setOpacity(0.5)
    placeholder_label.setGraphicsEffect(opacity_effect)
    placeholder_label.setStyleSheet("font-size:24px;font-weight:500;font-family: 'Segoe UI';")
    placeholder_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    placeholder_label.setText("Waiting for active window...")
        
    name_label = QLabel()
    name_label.setStyleSheet("font-size:18px;font-weight:600;font-family: 'Segoe UI';")
    name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    
    proccess_label = QLabel()
    proccess_label.setStyleSheet("font-size:12px;font-weight:600;font-family:'Segoe UI';")
    proccess_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    icon_label = QLabel()
    icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    icon_label.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
    icon_label.customContextMenuRequested.connect(lambda pos: show_context_menu(pos))
    icon_label.setStyleSheet("margin-top: 10px; margin-bottom: 10px")
    
    icon_label_desc = QLabel()
    opacity_effect = QGraphicsOpacityEffect()
    opacity_effect.setOpacity(0.5)
    icon_label_desc.setGraphicsEffect(opacity_effect)
    icon_label_desc.hide()
    icon_label_desc.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    icon_label_desc.setStyleSheet("font-size:11px; font-weight:500;font-family: 'Segoe UI';")
    icon_label_desc.setText("Right-click the icon to save as file")
    
    layout.addWidget(placeholder_label)
    layout.addWidget(name_label)
    layout.addWidget(proccess_label)
    layout.addWidget(icon_label)
    layout.addWidget(icon_label_desc)
    
    # New: Label above the button group
    size_label = QtWidgets.QLabel("Click a button to change icon size")
    size_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    opacity_effect2 = QGraphicsOpacityEffect()
    opacity_effect2.setOpacity(0.5)
    size_label.setGraphicsEffect(opacity_effect2)
    size_label.setStyleSheet("font-size:13px; font-weight:500;font-family: 'Segoe UI';")
    layout.addWidget(size_label)
    # New: Create icon size selection buttons and group them
    icon_size = 32  # default icon size
    latest_process = None
    latest_hwnd = None

    # When creating the buttons, add a stylesheet so the :checked state stays visible.
    button_layout = QtWidgets.QHBoxLayout()
    # Center the buttons to avoid full-width stretching
    button_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    
    btn16 = QtWidgets.QPushButton("16x16")
    btn24 = QtWidgets.QPushButton("24x24")
    btn32 = QtWidgets.QPushButton("32x32")
    btn16.setCheckable(True)
    btn24.setCheckable(True)
    btn32.setCheckable(True)
    # Set default to 32x32
    btn32.setChecked(True)

    # Set fixed width for each button to 40px and a fixed size policy
    btn16.setFixedWidth(60)
    btn16.setSizePolicy(QtWidgets.QSizePolicy(
        QtWidgets.QSizePolicy.Policy.Fixed,
        QtWidgets.QSizePolicy.Policy.Fixed))
    btn24.setFixedWidth(60)
    btn24.setSizePolicy(QtWidgets.QSizePolicy(
        QtWidgets.QSizePolicy.Policy.Fixed,
        QtWidgets.QSizePolicy.Policy.Fixed))
    btn32.setFixedWidth(60)
    btn32.setSizePolicy(QtWidgets.QSizePolicy(
        QtWidgets.QSizePolicy.Policy.Fixed,
        QtWidgets.QSizePolicy.Policy.Fixed))

    # Set stylesheet so the checked button remains visibly blue even if unfocused.
    style = """
    QPushButton {
        background-color: #4e4e4e;
        color: white;
        font-size: 13px;
        font-family: 'Segoe UI';
        border: none;
        border-radius: 3px;
        padding: 5px 10px;
    }
    QPushButton:hover {
        background-color: #4cc2ff;
        color: black;
    }
    QPushButton:pressed {
        background-color: #3399FF;
    }
    QPushButton:checked, QPushButton:!active:checked {
        background-color: #4cc2ff;
        color: black;
    }
    """
    btn16.setStyleSheet(style)
    btn24.setStyleSheet(style)
    btn32.setStyleSheet(style)

    button_layout.addWidget(btn16)
    button_layout.addWidget(btn24)
    button_layout.addWidget(btn32)
    layout.addLayout(button_layout)

    button_group = QtWidgets.QButtonGroup(window)
    button_group.setExclusive(True)
    button_group.addButton(btn16)
    button_group.addButton(btn24)
    button_group.addButton(btn32)

    def set_icon_size(new_size):
        nonlocal icon_size, latest_process, latest_hwnd
        icon_size = new_size
        # Force reload icon regardless of foreground.
        if latest_process and latest_hwnd:
            update_label(latest_process, latest_hwnd, force_reload=True)

    btn16.clicked.connect(lambda: set_icon_size(16))
    btn24.clicked.connect(lambda: set_icon_size(24))
    btn32.clicked.connect(lambda: set_icon_size(32))

    window.setLayout(layout)
    
    own_hwnd = int(window.winId())
    own_pid = os.getpid()  # Get the current process ID

    listener = EventListener(own_pid)  # Pass own_pid to EventListener

    def show_context_menu(pos):
        menu = QtWidgets.QMenu(window)
        menu.setWindowFlags(menu.windowFlags() | QtCore.Qt.WindowType.NoDropShadowWindowHint)
        menu.setStyleSheet("""
            QMenu {
                font-size: 12px;
                font-family: 'Segoe UI';
                background-color: #333;
                border: 1px solid #333;
                outline: none;
            }
            QMenu::icon {
                width: 0px;
            }
            QMenu::item {
                padding: 6px 12px;
            }
            QMenu::item:selected {
                background-color: #444;
            }
        """)
        save_action = menu.addAction("Save as PNG")
        action = menu.exec(icon_label.mapToGlobal(pos))
        if action == save_action:
            save_image()

    def save_image():
        pixmap = icon_label.pixmap()
        if pixmap:
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                window, "Save Image", "", "PNG Files (*.png)"
            )
            if file_path:
                pixmap.save(file_path, "PNG")

    # Modify update_label to accept an optional force_reload parameter.
    def update_label(process_name, hwnd, force_reload=False):
        nonlocal latest_process, latest_hwnd
        # Save latest active window info for reloads later.
        latest_process = process_name
        latest_hwnd = hwnd

        if hwnd == own_hwnd:
            return
        update_retry_count = 0
        try:
            # Only check if window is foreground if not forcing a reload.
            if not force_reload and hwnd != win32gui.GetForegroundWindow():
                return
            if process_name:
                dpi = window.screen().devicePixelRatio()
                icon_img = get_window_icon(hwnd, 1)
                if process_name == "ApplicationFrameHost.exe" and not icon_img:
                    if update_retry_count < 10:
                        update_retry_count += 1 
                        QTimer.singleShot(500, lambda: update_label(process_name, hwnd))
                        return
                    else:
                        update_retry_count = 0
                if icon_img:
                    window_title = win32gui.GetWindowText(hwnd)
                    if window_title in IGNORED_TITLES:
                        return
                    placeholder_label.hide()
                    name_label.setText(window_title if len(window_title) <= 50 else window_title[:50] + '...')
                    proccess_label.setText(process_name)
                    # Use the nonlocal icon_size for resizing
                    icon_img = icon_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS).convert("RGBA")
                    qimage = QImage(icon_img.tobytes(), icon_img.width, icon_img.height, QImage.Format.Format_RGBA8888)
                    pixmap = QPixmap.fromImage(qimage)
                    pixmap.setDevicePixelRatio(dpi)
                    icon_label.setPixmap(pixmap)
                    icon_label_desc.show()
            else:
                name_label.setText("No active application")
        except Exception:
            logging.exception(f"Failed to update active window title for window with HWND {hwnd}")
            
    listener.focused_window_changed.connect(update_label)

    thread = threading.Thread(target=listener.hook, daemon=True)
    thread.start()

    def on_exit():
        os._exit(0)

    app.aboutToQuit.connect(on_exit)

    window.show()
    app.exec()

if __name__ == "__main__":
    main()