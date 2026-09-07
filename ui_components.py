"""Shared widgets and presentation for the desktop tools."""
from collections import deque
import threading

from PyQt5.QtCore import QThread, QTimer, pyqtSlot
from PyQt5.QtWidgets import QPlainTextEdit


class InterruptibleThread(QThread):
    """Wake polling delays immediately when a task is stopped."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_running = True
        self._stop_event = threading.Event()

    def msleep(self, milliseconds):
        self._stop_event.wait(max(0, milliseconds) / 1000)

    def stop(self):
        self.is_running = False
        self._stop_event.set()


class BufferedLogView(QPlainTextEdit):
    """Bound memory and batch updates without moving a reader's scroll position."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(3000)
        self.setUndoRedoEnabled(False)
        self._pending = deque(maxlen=3000)
        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self.flush)
        self._timer.start()

    @pyqtSlot(str)
    def append(self, message):
        self._pending.append(str(message))

    def flush(self):
        if not self._pending:
            return
        scrollbar = self.verticalScrollBar()
        position = scrollbar.value()
        follow = position >= scrollbar.maximum() - 2
        text = "\n".join(self._pending)
        self._pending.clear()
        self.appendPlainText(text)
        scrollbar.setValue(scrollbar.maximum() if follow else position)

    def clear(self):
        self._pending.clear()
        super().clear()


def workspace_style(dark):
    """Opaque surfaces keep contrast predictable and avoid nested frame painting."""
    if dark:
        bg, surface, field = "#101722", "#182231", "#111b29"
        text, muted, border = "#edf2fa", "#9cacc2", "#2a3a50"
        accent, hover, selected = "#5b8cff", "#76a0ff", "#263d62"
    else:
        bg, surface, field = "#f3f6fb", "#ffffff", "#f8faff"
        text, muted, border = "#19283e", "#607189", "#dce4ef"
        accent, hover, selected = "#3267db", "#2457c4", "#e4edff"
    return f'''
        QMainWindow, QDialog {{ background: {bg}; }}
        QWidget {{ color: {text}; font-family: "Microsoft YaHei UI"; font-size: 13px; }}
        QWidget#CentralWidget, QLabel {{ background: transparent; border: none; }}
        QFrame#Card, QGroupBox {{ background: {surface}; border: 1px solid {border}; border-radius: 12px; }}
        QGroupBox {{ margin-top: 12px; padding-top: 14px; }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 16px; padding: 0 5px; }}
        QLabel#Eyebrow {{ color: {accent}; font-size: 11px; font-weight: bold; }}
        QLabel#Title {{ font-size: 28px; font-weight: bold; }}
        QLabel#Muted {{ color: {muted}; }}
        QLabel#Metric {{ font-size: 24px; font-weight: bold; }}
        QLabel#Status {{ color: {accent}; background: {selected}; border-radius: 8px; padding: 8px 14px; }}
        QMenuBar, QMenu {{ background: {surface}; border: 1px solid {border}; }}
        QMenuBar::item {{ padding: 8px 14px; background: transparent; }}
        QMenu::item {{ padding: 8px 26px; }}
        QMenuBar::item:selected, QMenu::item:selected {{ background: {selected}; }}
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{ background: {field}; border: 1px solid {border}; border-radius: 7px; padding: 8px; selection-background-color: {accent}; }}
        QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{ border-color: {accent}; }}
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox QAbstractItemView {{ background: {surface}; color: {text}; selection-background-color: {selected}; selection-color: {text}; }}
        QPushButton {{ background: {surface}; border: 1px solid {border}; border-radius: 7px; padding: 9px 16px; font-weight: bold; }}
        QPushButton:hover {{ background: {selected}; border-color: {accent}; }}
        QPushButton:focus {{ border: 2px solid {accent}; }}
        QPushButton#Primary {{ background: {accent}; color: white; border: none; }}
        QPushButton#Primary:hover {{ background: {hover}; }}
        QPushButton#Primary[running="true"] {{ background: #c94555; }}
        QPushButton:disabled {{ color: {muted}; background: {field}; border-color: {border}; }}
        QListWidget, QTableView, QTreeView {{ background: {field}; alternate-background-color: {surface}; border: 1px solid {border}; border-radius: 8px; outline: none; gridline-color: {border}; selection-background-color: {selected}; selection-color: {text}; }}
        QListWidget::item {{ padding: 12px; border-bottom: 1px solid {border}; }}
        QListWidget::item:selected, QTableView::item:selected, QTreeView::item:selected {{ background: {selected}; color: {text}; }}
        QHeaderView::section {{ background: {surface}; color: {muted}; border: none; border-bottom: 1px solid {border}; padding: 10px 6px; font-weight: bold; }}
        QTableCornerButton::section {{ background: {surface}; border: none; }}
        QTabWidget::pane {{ border: none; }}
        QTabBar::tab {{ color: {muted}; background: transparent; padding: 12px 20px; border-bottom: 2px solid transparent; }}
        QTabBar::tab:selected {{ color: {accent}; border-bottom-color: {accent}; }}
        QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
        QScrollBar::handle:vertical {{ background: {border}; border-radius: 5px; min-height: 30px; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        QStatusBar {{ color: {muted}; background: {surface}; border-top: 1px solid {border}; }}
        QToolTip {{ color: {text}; background: {surface}; border: 1px solid {border}; padding: 6px; }}
    '''
