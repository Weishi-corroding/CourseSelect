# -*- coding: utf-8 -*-
"""自定义 UI 组件模块 - Modern Tech Style (兼容修复版)"""

from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QMenu, QAction
from PyQt5.QtGui import QFont, QCursor
from PyQt5.QtCore import Qt, QSize

# --- 1. 安全导入与兼容性补丁 ---
try:
    from config import NORD_THEME
except ImportError:
    NORD_THEME = {}

# 定义本 UI 需要的所有颜色默认值
_DEFAULT_COLORS = {
    'bg': '#2E3440',
    'primary': '#3B4252',
    'secondary': '#4C566A',
    'accent': '#88C0D0',       # 修复报错的关键：补充缺失的强调色
    'text_primary': '#ECEFF4',
    'text_secondary': '#D8DEE9',
    'accent_error': '#BF616A'
}

# 自动补全 config 中可能缺失的键值，防止 KeyError
for key, value in _DEFAULT_COLORS.items():
    if key not in NORD_THEME:
        NORD_THEME[key] = value

# --------------------------------

class CustomMenuBar(QWidget):
    """自定义菜单栏 - 现代科技风格"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.drag_position = None
        
        # --- 整体样式设置 ---
        self.setFixedHeight(40) # 稍微增加高度，更显大气
        # 底部增加一条细微的分割线，增强科技感
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {NORD_THEME['primary']};
                border-bottom: 1px solid {NORD_THEME['secondary']}; 
                font-family: 'Segoe UI', 'Microsoft YaHei UI', 'PingFang SC', sans-serif;
            }}
            QToolTip {{
                color: {NORD_THEME['text_primary']};
                background-color: {NORD_THEME['bg']};
                border: 1px solid {NORD_THEME['accent']};
            }}
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 0, 0, 0) # 左侧留一点呼吸感
        layout.setSpacing(8) # 按钮之间的间距
        
        # --- Logo 按钮 ---
        self.logo_btn = QPushButton("🎓 菜单") # 加上文字让它更像一个功能入口
        self.logo_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.logo_btn.setFixedSize(80, 30)
        self.logo_btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
        # 样式：平时透明，悬停时微亮，并带有科技蓝边框暗示
        self.logo_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {NORD_THEME['text_primary']};
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 0 5px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {NORD_THEME['secondary']};
                border: 1px solid {NORD_THEME['secondary']};
            }}
            QPushButton:pressed {{
                background-color: {NORD_THEME['bg']};
                color: {NORD_THEME['accent']};
            }}
            QPushButton::menu-indicator {{ 
                image: none; /* 隐藏默认的下拉小三角，保持简洁 */
            }}
        """)
        
        # --- 菜单样式 (统一提取) ---
        # 这种样式看起来像悬浮的卡片，带有边框和 padding
        menu_stylesheet = f"""
            QMenu {{
                background-color: {NORD_THEME['bg']};
                color: {NORD_THEME['text_primary']};
                border: 1px solid {NORD_THEME['secondary']};
                border-radius: 6px;
                padding: 5px 0px;
            }}
            QMenu::item {{
                background-color: transparent;
                padding: 6px 20px 6px 30px; /* 增加舒适的点击区域 */
                margin: 2px 5px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: {NORD_THEME['secondary']};
                color: {NORD_THEME['text_primary']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {NORD_THEME['secondary']};
                margin: 4px 10px;
            }}
        """

        # 创建菜单
        self.menu = QMenu(self)
        self.menu.setStyleSheet(menu_stylesheet)
        
        # 新建菜单
        new_menu = self.menu.addMenu("  📂  新建")
        new_menu.setStyleSheet(menu_stylesheet)
        
        self.new_course_action = QAction("课程列表", self)
        self.new_account_action = QAction("选课人", self)
        self.new_delete_course_action = QAction("待删除课程", self)
        self.update_cookie_action = QAction("更新 Cookie", self)
        new_menu.addAction(self.new_course_action)
        new_menu.addAction(self.new_account_action)
        new_menu.addAction(self.new_delete_course_action)
        new_menu.addSeparator() # 分割线
        new_menu.addAction(self.update_cookie_action)
        
        # 导入菜单
        import_menu = self.menu.addMenu("  📥  导入")
        import_menu.setStyleSheet(menu_stylesheet)
        
        self.import_courses_action = QAction("课程文件", self)
        self.import_cookies_action = QAction("Cookie 文件", self)
        self.import_accounts_action = QAction("选课人文件", self)
        import_menu.addAction(self.import_courses_action)
        import_menu.addAction(self.import_cookies_action)
        import_menu.addAction(self.import_accounts_action)
        
        # 设置菜单
        self.menu.addSeparator()
        self.settings_action = QAction("  ⚙️  设置", self)
        self.menu.addAction(self.settings_action)
        
        self.logo_btn.setMenu(self.menu)
        layout.addWidget(self.logo_btn)
        
        # 弹簧
        layout.addStretch()
        
        # --- 窗口控制按钮组 ---
        # 定义一个通用的窗口按钮样式函数，方便统一修改
        def get_window_btn_style(hover_color, normal_bg="transparent"):
            return f"""
                QPushButton {{
                    background-color: {normal_bg};
                    color: {NORD_THEME['text_secondary']};
                    border: none;
                    border-radius: 0px; /* 窗口控制按钮通常不需要圆角，或者很小 */
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                    color: #FFFFFF;
                }}
                QPushButton:pressed {{
                    background-color: {NORD_THEME['bg']};
                }}
            """

        btn_size = QSize(46, 40) # 更宽的点击区域，贴合屏幕边缘
        btn_font = QFont("Segoe UI Symbol", 10) # 使用符号字体，符号显示更标准

        # 最小化按钮
        self.minimize_btn = QPushButton("─") # 使用 Unicode 细横线
        self.minimize_btn.setFont(btn_font)
        self.minimize_btn.setFixedSize(btn_size)
        self.minimize_btn.setStyleSheet(get_window_btn_style(NORD_THEME['secondary']))
        self.minimize_btn.clicked.connect(self.minimize_window)
        layout.addWidget(self.minimize_btn)
        
        # 最大化按钮
        self.maximize_btn = QPushButton("❐") # 使用 Unicode 窗口图标
        self.maximize_btn.setFont(btn_font)
        self.maximize_btn.setFixedSize(btn_size)
        self.maximize_btn.setStyleSheet(get_window_btn_style(NORD_THEME['secondary']))
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        layout.addWidget(self.maximize_btn)
        
        # 关闭按钮 (特殊的红色 hover)
        self.close_btn = QPushButton("✕")
        self.close_btn.setFont(btn_font)
        self.close_btn.setFixedSize(btn_size)
        # 关闭按钮 hover 时显示红色
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {NORD_THEME['text_secondary']};
                border: none;
            }}
            QPushButton:hover {{
                background-color: {NORD_THEME['accent_error']}; /* 红色警告 */
                color: white;
            }}
            QPushButton:pressed {{
                background-color: #B04050;
            }}
        """)
        self.close_btn.clicked.connect(self.close_window)
        layout.addWidget(self.close_btn)
        
        layout.setSpacing(0) # 全局紧凑
        self.logo_btn.setStyleSheet(self.logo_btn.styleSheet() + "margin-right: 10px;") # 给 Logo 补一点右边距
        
        self.setLayout(layout)

    def minimize_window(self):
        self.parent_window.showMinimized()
    
    def toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.maximize_btn.setText("❐")
        else:
            self.parent_window.showMaximized()
            self.maximize_btn.setText("❒") # 切换图标
    
    def close_window(self):
        self.parent_window.close()
    
    def mousePressEvent(self, event):
        """处理拖动"""
        if event.button() == Qt.LeftButton:
            # 只有在非按钮区域点击才能拖动，防止误触
            child = self.childAt(event.pos())
            if not child or child == self:
                self.drag_position = event.globalPos() - self.parent_window.frameGeometry().topLeft()
                event.accept()
    
    def mouseMoveEvent(self, event):
        """拖动窗口"""
        if self.drag_position is not None and event.buttons() == Qt.LeftButton:
            self.parent_window.move(event.globalPos() - self.drag_position)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        self.drag_position = None