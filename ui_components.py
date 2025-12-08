# -*- coding: utf-8 -*-
"""自定义 UI 组件模块"""

from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QMenu, QAction
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from config import NORD_THEME


class CustomMenuBar(QWidget):
    """自定义菜单栏 - logo 作为菜单按钮"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.drag_position = None
        
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Logo 按钮 - 点击弹出菜单
        self.logo_btn = QPushButton("🎓")
        self.logo_btn.setFont(QFont("Arial", 14))
        self.logo_btn.setFixedSize(40, 32)
        self.logo_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NORD_THEME['primary']};
                color: {NORD_THEME['text_secondary']};
                border: none;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {NORD_THEME['secondary']};
            }}
            QPushButton:pressed {{
                background-color: {NORD_THEME['bg']};
            }}
        """)
        
        # 创建菜单
        self.menu = QMenu(self)
        self.menu.setStyleSheet(f"""
            QMenu {{
                background-color: {NORD_THEME['primary']};
                color: {NORD_THEME['text_primary']};
                border: 1px solid {NORD_THEME['secondary']};
            }}
            QMenu::item:selected {{
                background-color: {NORD_THEME['secondary']};
            }}
        """)
        
        # 新建菜单
        new_menu = self.menu.addMenu("新建")
        new_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {NORD_THEME['primary']};
                color: {NORD_THEME['text_primary']};
                border: 1px solid {NORD_THEME['secondary']};
            }}
            QMenu::item:selected {{
                background-color: {NORD_THEME['secondary']};
            }}
        """)
        
        self.new_course_action = QAction("课程列表", self)
        self.new_account_action = QAction("选课人", self)
        self.update_cookie_action = QAction("更新 Cookie", self)
        new_menu.addAction(self.new_course_action)
        new_menu.addAction(self.new_account_action)
        new_menu.addAction(self.update_cookie_action)
        
        # 导入菜单
        import_menu = self.menu.addMenu("导入")
        import_menu.setStyleSheet(f"""
            QMenu {{
                background-color: {NORD_THEME['primary']};
                color: {NORD_THEME['text_primary']};
                border: 1px solid {NORD_THEME['secondary']};
            }}
            QMenu::item:selected {{
                background-color: {NORD_THEME['secondary']};
            }}
        """)
        
        self.import_courses_action = QAction("课程文件", self)
        self.import_cookies_action = QAction("Cookie 文件", self)
        self.import_accounts_action = QAction("选课人文件", self)
        import_menu.addAction(self.import_courses_action)
        import_menu.addAction(self.import_cookies_action)
        import_menu.addAction(self.import_accounts_action)
        
        # 设置菜单
        self.menu.addSeparator()
        self.settings_action = QAction("⚙️ 设置", self)
        self.menu.addAction(self.settings_action)
        
        self.logo_btn.setMenu(self.menu)
        layout.addWidget(self.logo_btn)
        
        # 弹簧（占用空间）
        layout.addStretch()
        
        # 最小化按钮
        self.minimize_btn = QPushButton("−")
        self.minimize_btn.setFont(QFont("Arial", 12))
        self.minimize_btn.setFixedSize(40, 32)
        self.minimize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NORD_THEME['primary']};
                color: {NORD_THEME['text_secondary']};
                border: none;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {NORD_THEME['secondary']};
            }}
            QPushButton:pressed {{
                background-color: {NORD_THEME['bg']};
            }}
        """)
        self.minimize_btn.clicked.connect(self.minimize_window)
        layout.addWidget(self.minimize_btn)
        
        # 最大化按钮
        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFont(QFont("Arial", 12))
        self.maximize_btn.setFixedSize(40, 32)
        self.maximize_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {NORD_THEME['primary']};
                color: {NORD_THEME['text_secondary']};
                border: none;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {NORD_THEME['secondary']};
            }}
            QPushButton:pressed {{
                background-color: {NORD_THEME['bg']};
            }}
        """)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        layout.addWidget(self.maximize_btn)
        
        # 关闭按钮
        self.close_btn = QPushButton("✕")
        self.close_btn.setFont(QFont("Arial", 12))
        self.close_btn.setFixedSize(40, 32)
        self.close_btn.setStyleSheet(f"""
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
        self.close_btn.clicked.connect(self.close_window)
        layout.addWidget(self.close_btn)
        
        self.setLayout(layout)
        self.setFixedHeight(32)
        self.setStyleSheet(f"background-color: {NORD_THEME['primary']};")
    
    def minimize_window(self):
        self.parent_window.showMinimized()
    
    def toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()
    
    def close_window(self):
        self.parent_window.close()
    
    def mousePressEvent(self, event):
        """处理拖动"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.parent_window.frameGeometry().topLeft()
    
    def mouseMoveEvent(self, event):
        """拖动窗口"""
        if self.drag_position is not None and event.buttons() == Qt.LeftButton:
            self.parent_window.move(event.globalPos() - self.drag_position)
