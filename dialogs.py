# -*- coding: utf-8 -*-
"""自定义对话框和输入框 - 应用样式表"""

from PyQt5.QtWidgets import (
    QInputDialog, QMessageBox, QDialog, QVBoxLayout, QLabel, 
    QLineEdit, QTextEdit, QPushButton, QHBoxLayout, QWidget
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QPoint
from config import APP_STYLESHEET, NORD_THEME


class DialogTitleBar(QWidget):
    """无边框对话框的自定义标题栏"""
    
    def __init__(self, dialog, title="", parent=None):
        super().__init__(parent)
        self.dialog = dialog
        self.drag_position = None
        self.setFixedHeight(32)
        self.setStyleSheet(f"background-color: {NORD_THEME['primary']};")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 11, QFont.Bold))
        title_label.setStyleSheet(f"color: {NORD_THEME['text_primary']};")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFont(QFont("Arial", 11))
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NORD_THEME['primary']};
                color: {NORD_THEME['accent_error']};
                border: none;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {NORD_THEME['accent_error']};
                color: {NORD_THEME['bg']};
            }}
            QPushButton:pressed {{
                background-color: #A53860;
            }}
        """)
        close_btn.clicked.connect(dialog.reject)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
    
    def mousePressEvent(self, event):
        """处理拖动"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.dialog.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        """拖动窗口"""
        if self.drag_position is not None and event.buttons() == Qt.LeftButton:
            self.dialog.move(event.globalPos() - self.drag_position)


class StyledInputDialog(QInputDialog):
    """应用样式表的输入对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(APP_STYLESHEET)
        # 移除 Windows 默认标题栏
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)


class StyledMessageBox(QMessageBox):
    """应用样式表的消息框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(APP_STYLESHEET)
        # 移除 Windows 默认标题栏
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
    
    @staticmethod
    def information(parent, title, text):
        """信息提示框"""
        box = StyledMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(QMessageBox.Information)
        box.exec_()
    
    @staticmethod
    def warning(parent, title, text):
        """警告提示框"""
        box = StyledMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(QMessageBox.Warning)
        box.exec_()
    
    @staticmethod
    def critical(parent, title, text):
        """错误提示框"""
        box = StyledMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(QMessageBox.Critical)
        box.exec_()


def get_text_input(parent, title, label):
    """获取单行文本输入"""
    dialog = StyledInputDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setLabelText(label)
    dialog.setInputMode(QInputDialog.TextInput)
    dialog.resize(400, 150)
    
    ok = dialog.exec_() == QInputDialog.Accepted
    text = dialog.textValue() if ok else ""
    return text, ok


def get_multiline_input(parent, title, label):
    """获取多行文本输入"""
    # 创建自定义对话框以支持多行输入
    custom_dialog = QDialog(parent)
    custom_dialog.setWindowTitle(title)
    custom_dialog.setStyleSheet(APP_STYLESHEET)
    custom_dialog.resize(500, 350)
    # 移除 Windows 默认标题栏
    custom_dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
    
    # 主布局
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)
    
    # 自定义标题栏
    title_bar = DialogTitleBar(custom_dialog, title)
    main_layout.addWidget(title_bar)
    
    # 内容布局
    content_layout = QVBoxLayout()
    content_layout.setContentsMargins(12, 12, 12, 12)
    
    label_widget = QLabel(label)
    label_widget.setFont(QFont("Arial", 11))
    content_layout.addWidget(label_widget)
    
    text_edit = QTextEdit()
    text_edit.setFont(QFont("Consolas", 10))
    content_layout.addWidget(text_edit)
    
    button_layout = QHBoxLayout()
    ok_btn = QPushButton("确定")
    cancel_btn = QPushButton("取消")
    
    ok_btn.clicked.connect(custom_dialog.accept)
    cancel_btn.clicked.connect(custom_dialog.reject)
    
    button_layout.addStretch()
    button_layout.addWidget(ok_btn)
    button_layout.addWidget(cancel_btn)
    
    content_layout.addLayout(button_layout)
    main_layout.addLayout(content_layout)
    
    custom_dialog.setLayout(main_layout)
    
    ok = custom_dialog.exec_() == QDialog.Accepted
    text = text_edit.toPlainText() if ok else ""
    return text, ok


def get_account_input(parent, title="新建选课人"):
    """获取账户信息输入（姓名、学号、密码在同一窗口）"""
    custom_dialog = QDialog(parent)
    custom_dialog.setWindowTitle(title)
    custom_dialog.setStyleSheet(APP_STYLESHEET)
    custom_dialog.resize(450, 300)
    custom_dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
    
    # 主布局
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)
    
    # 自定义标题栏
    title_bar = DialogTitleBar(custom_dialog, title)
    main_layout.addWidget(title_bar)
    
    # 内容布局
    content_layout = QVBoxLayout()
    content_layout.setContentsMargins(12, 12, 12, 12)
    content_layout.setSpacing(10)
    
    # 姓名
    name_label = QLabel("姓名:")
    name_label.setFont(QFont("Arial", 11))
    content_layout.addWidget(name_label)
    name_input = QLineEdit()
    name_input.setFont(QFont("Arial", 10))
    content_layout.addWidget(name_input)
    
    # 学号
    username_label = QLabel("学号:")
    username_label.setFont(QFont("Arial", 11))
    content_layout.addWidget(username_label)
    username_input = QLineEdit()
    username_input.setFont(QFont("Arial", 10))
    content_layout.addWidget(username_input)
    
    # 密码
    password_label = QLabel("密码:")
    password_label.setFont(QFont("Arial", 11))
    content_layout.addWidget(password_label)
    password_input = QLineEdit()
    password_input.setFont(QFont("Arial", 10))
    password_input.setEchoMode(QLineEdit.Password)
    content_layout.addWidget(password_input)
    
    content_layout.addStretch()
    
    # 按钮
    button_layout = QHBoxLayout()
    ok_btn = QPushButton("确定")
    cancel_btn = QPushButton("取消")
    
    ok_btn.clicked.connect(custom_dialog.accept)
    cancel_btn.clicked.connect(custom_dialog.reject)
    
    button_layout.addStretch()
    button_layout.addWidget(ok_btn)
    button_layout.addWidget(cancel_btn)
    
    content_layout.addLayout(button_layout)
    main_layout.addLayout(content_layout)
    
    custom_dialog.setLayout(main_layout)
    
    ok = custom_dialog.exec_() == QDialog.Accepted
    if ok:
        return (
            name_input.text().strip(),
            username_input.text().strip(),
            password_input.text(),
            True
        )
    return ("", "", "", False)


def get_settings_input(parent, current_interval=2, title="设置"):
    """获取程序设置（请求间隔）"""
    custom_dialog = QDialog(parent)
    custom_dialog.setWindowTitle(title)
    custom_dialog.setStyleSheet(APP_STYLESHEET)
    custom_dialog.resize(400, 250)
    custom_dialog.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
    
    # 主布局
    main_layout = QVBoxLayout()
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)
    
    # 自定义标题栏
    title_bar = DialogTitleBar(custom_dialog, title)
    main_layout.addWidget(title_bar)
    
    # 内容布局
    content_layout = QVBoxLayout()
    content_layout.setContentsMargins(12, 12, 12, 12)
    content_layout.setSpacing(10)
    
    # 请求间隔
    interval_label = QLabel("请求间隔 (秒):")
    interval_label.setFont(QFont("Arial", 11))
    content_layout.addWidget(interval_label)
    
    interval_input = QLineEdit()
    interval_input.setFont(QFont("Arial", 10))
    interval_input.setText(str(current_interval))
    interval_input.setMaximumWidth(100)
    content_layout.addWidget(interval_input)
    
    info_label = QLabel("每次课程选择请求之间的等待时间")
    info_label.setFont(QFont("Arial", 9))
    info_label.setStyleSheet(f"color: {NORD_THEME['text_secondary']};")
    content_layout.addWidget(info_label)
    
    content_layout.addStretch()
    
    # 按钮
    button_layout = QHBoxLayout()
    ok_btn = QPushButton("确定")
    cancel_btn = QPushButton("取消")
    
    ok_btn.clicked.connect(custom_dialog.accept)
    cancel_btn.clicked.connect(custom_dialog.reject)
    
    button_layout.addStretch()
    button_layout.addWidget(ok_btn)
    button_layout.addWidget(cancel_btn)
    
    content_layout.addLayout(button_layout)
    main_layout.addLayout(content_layout)
    
    custom_dialog.setLayout(main_layout)
    
    ok = custom_dialog.exec_() == QDialog.Accepted
    if ok:
        try:
            interval = float(interval_input.text())
            if interval < 0.1:
                interval = 0.1
            return interval, True
        except ValueError:
            return current_interval, False
    return current_interval, False

