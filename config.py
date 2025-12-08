# -*- coding: utf-8 -*-
"""配置和常量定义"""

# 颜色主题 - Nord Dark Theme
NORD_THEME = {
    "bg": "#2E3440",
    "primary": "#3B4252",
    "secondary": "#434C5E",
    "accent_success": "#A3BE8C",
    "accent_error": "#BF616A",
    "text_primary": "#ECEFF4",
    "text_secondary": "#D8DEE9",
    "accent_info": "#88C0D0",
}

# 全局样式表
APP_STYLESHEET = """
QMainWindow {
    background-color: #2E3440;
}
QMenuBar {
    background-color: #3B4252;
    color: #ECEFF4;
    border: none;
}
QMenuBar::item:selected {
    background-color: #434C5E;
}
QMenu {
    background-color: #3B4252;
    color: #ECEFF4;
    border: 1px solid #434C5E;
}
QMenu::item:selected {
    background-color: #434C5E;
}
QLabel {
    color: #D8DEE9;
    background-color: transparent;
}
QComboBox {
    background-color: #3B4252;
    color: #ECEFF4;
    border: 1px solid #434C5E;
    border-radius: 4px;
    padding: 5px;
}
QComboBox::drop-down {
    border: none;
    background-color: #434C5E;
}
QComboBox QAbstractItemView {
    background-color: #3B4252;
    color: #ECEFF4;
    selection-background-color: #434C5E;
}
QTextEdit {
    background-color: #3B4252;
    color: #ECEFF4;
    border: 1px solid #434C5E;
    border-radius: 4px;
}
QLineEdit {
    background-color: #3B4252;
    color: #ECEFF4;
    border: 1px solid #434C5E;
    border-radius: 4px;
    padding: 5px;
}
QPushButton {
    background-color: #A3BE8C;
    color: #2E3440;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #B8D896;
}
QPushButton:pressed {
    background-color: #95B475;
}
QDialog {
    background-color: #2E3440;
}
QMessageBox {
    background-color: #2E3440;
}
QMessageBox QLabel {
    color: #D8DEE9;
}
"""

# 文件配置
FILES = {
    "accounts": "accounts.json",
    "courses": "courses.json",
    "cookies": "cookies.json",
}

# 学选课系统 URL
LOGIN_URL = "https://jwgl.dhu.edu.cn/dhu/casLogin"
COURSE_SUBMIT_URL = "https://jwgl.dhu.edu.cn/dhu/selectcourse/scSubmit"
