# -*- coding: utf-8 -*-
"""主程序 - 应用入口和主窗口"""

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QTextEdit, QPushButton, QFileDialog
)
from PyQt5.QtGui import QFont, QIcon
import sys
import os
from PyQt5.QtCore import Qt
import json

from config import APP_STYLESHEET, FILES, NORD_THEME
from ui_components import CustomMenuBar
from dialogs import StyledMessageBox, get_text_input, get_multiline_input
from threads import CourseSelectionThread
from core import (
    load_accounts, save_accounts, load_courses, save_courses,
    load_cookies_dict, save_cookies_dict, load_delete_courses, save_delete_courses
)


class MainWindow(QMainWindow):
    """主应用窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能选课系统")
        self.setGeometry(100, 100, 900, 650)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet(APP_STYLESHEET)
        
        # 创建自定义菜单栏
        self.menu_bar = CustomMenuBar(self)
        
        # 连接菜单项信号
        self.menu_bar.import_courses_action.triggered.connect(self.import_courses_file)
        self.menu_bar.import_cookies_action.triggered.connect(self.import_cookies_file)
        self.menu_bar.import_accounts_action.triggered.connect(self.import_accounts_file)
        self.menu_bar.new_course_action.triggered.connect(self.new_course_list)
        self.menu_bar.new_account_action.triggered.connect(self.new_account_dialog)
        self.menu_bar.new_delete_course_action.triggered.connect(self.new_delete_course_list)
        self.menu_bar.update_cookie_action.triggered.connect(self.update_cookie_for_user)
        self.menu_bar.settings_action.triggered.connect(self.show_settings)
        
        # 创建主容器
        main_container = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 添加自定义菜单栏
        main_layout.addWidget(self.menu_bar)
        
        # 创建内容布局
        self.layout = QVBoxLayout()
        
        # 标题
        self.title_label = QLabel("智能选课系统")
        self.title_label.setFont(QFont("Arial", 20, QFont.Bold))
        self.title_label.setStyleSheet(f"color: {NORD_THEME['accent_info']}; padding: 16px 0px;")
        self.layout.addWidget(self.title_label, alignment=Qt.AlignCenter)
        
        # 选择抢课人
        self.user_label = QLabel("选择抢课人:")
        self.user_label.setFont(QFont("Arial", 12))
        self.layout.addWidget(self.user_label)
        
        self.user_combo = QComboBox()
        self.layout.addWidget(self.user_combo)
        
        # 添加占位符提示（启动时显示为空）
        self.user_combo.addItem("")  # 空选项作为初始值
        
        # 用户信息显示
        self.user_info_label = QLabel("")
        self.user_info_label.setFont(QFont("Arial", 11))
        self.layout.addWidget(self.user_info_label)
        
        # 课程列表显示区域 - 拆分为左右两个窗口
        courses_layout = QHBoxLayout()
        
        # 左边：待选课程
        left_layout = QVBoxLayout()
        self.course_info_label = QLabel("待选课程:")
        self.course_info_label.setFont(QFont("Arial", 11))
        left_layout.addWidget(self.course_info_label)
        
        self.course_display = QTextEdit()
        self.course_display.setReadOnly(True)
        left_layout.addWidget(self.course_display)
        
        # 右边：待删除课程
        right_layout = QVBoxLayout()
        self.delete_course_info_label = QLabel("待删除课程:")
        self.delete_course_info_label.setFont(QFont("Arial", 11))
        right_layout.addWidget(self.delete_course_info_label)
        
        self.delete_course_display = QTextEdit()
        self.delete_course_display.setReadOnly(True)
        right_layout.addWidget(self.delete_course_display)
        
        # 将左右两个布局添加到水平布局中
        courses_layout.addLayout(left_layout)
        courses_layout.addLayout(right_layout)
        self.layout.addLayout(courses_layout)
        
        # 注意：启动时不加载用户，保持下拉菜单为空
        # self.load_users()
        
        # 连接信号（必须在所有 UI 元素创建之后）
        self.user_combo.currentTextChanged.connect(self.on_user_selected)
        
        # 状态显示
        self.status_box = QTextEdit()
        self.status_box.setReadOnly(True)
        self.layout.addWidget(self.status_box)
        
        # 按钮布局（开始/停止按钮）
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("开始选课")
        self.start_button.setFont(QFont("Arial", 14, QFont.Bold))
        self.start_button.clicked.connect(self.toggle_selection)
        button_layout.addWidget(self.start_button)
        
        self.layout.addLayout(button_layout)
        
        # 将内容布局添加到主布局
        main_layout.addLayout(self.layout)
        main_container.setLayout(main_layout)
        self.setCentralWidget(main_container)
        
        # 配置变量
        self.request_interval = 2  # 默认请求间隔(秒)
        self.thread = None
    
    def on_user_selected(self, username):
        """当下拉菜单选择变化时，显示用户信息和课程列表"""
        if not username:
            self.user_info_label.setText("")
            self.course_display.setText("")
            self.delete_course_display.setText("")
            return
        
        # 读取并显示用户信息
        try:
            accounts = load_accounts()
            user_acc = next((acc for acc in accounts if acc["name"] == username), None)
            if user_acc:
                self.user_info_label.setText(
                    f"学号: {user_acc['username']}  |  密码: {user_acc['password']}"
                )
        except Exception:
            self.user_info_label.setText("")
        
        # 读取并显示该用户的待选课程列表
        try:
            courses_data = load_courses()
            courses = courses_data.get(username, [])
            if courses:
                self.course_display.setText("\n".join(str(c) for c in courses))
            else:
                self.course_display.setText(f"(未在 courses.json 中找到该用户的课程列表)")
        except Exception:
            self.course_display.setText("(未找到 courses.json 或读取失败)")
        
        # 读取并显示该用户的待删除课程列表
        try:
            from core import load_delete_courses
            delete_courses_data = load_delete_courses()
            delete_courses = delete_courses_data.get(username, [])
            if delete_courses:
                delete_courses_str = "\n".join(
                    f"{c['courseCode']} (班序:{c['classNo']})" for c in delete_courses
                )
                self.delete_course_display.setText(delete_courses_str)
            else:
                self.delete_course_display.setText("(无待删除课程)")
        except Exception:
            self.delete_course_display.setText("(未找到 delete_courses.json 或读取失败)")
    
    def load_users(self):
        """加载用户列表到下拉框"""
        try:
            accounts = load_accounts()
            for acc in accounts:
                self.user_combo.addItem(acc["name"])
        except Exception:
            pass
    
    def import_courses_file(self):
        """导入课程列表文件"""
        file_path = QFileDialog.getOpenFileName(
            self, 
            "选择课程列表 JSON (格式: {\"用户名\": [课程编号, ...]})", 
            "", 
            "JSON Files (*.json)"
        )[0]
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            save_courses(data)
            StyledMessageBox.information(self, "导入成功", "已更新本地 courses.json 文件")
        except Exception as e:
            StyledMessageBox.warning(self, "导入失败", f"无法读取或写入文件: {e}")
    
    def import_cookies_file(self):
        """导入 Cookies 文件"""
        file_path = QFileDialog.getOpenFileName(
            self, 
            "选择 cookies.json", 
            "", 
            "JSON Files (*.json)"
        )[0]
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            save_cookies_dict(data)
            StyledMessageBox.information(self, "导入成功", "已更新本地 cookies.json 文件")
        except Exception as e:
            StyledMessageBox.warning(self, "导入失败", f"无法读取或写入文件: {e}")
    
    def import_accounts_file(self):
        """导入账户文件"""
        file_path = QFileDialog.getOpenFileName(
            self, 
            "选择 accounts.json", 
            "", 
            "JSON Files (*.json)"
        )[0]
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            save_accounts(data.get("accounts", []))
            
            # 刷新下拉
            self.user_combo.clear()
            for acc in data.get("accounts", []):
                self.user_combo.addItem(acc.get("name"))
            
            StyledMessageBox.information(self, "导入成功", "已更新本地 accounts.json 并刷新列表")
        except Exception as e:
            StyledMessageBox.warning(self, "导入失败", f"无法读取或写入文件: {e}")
    
    def new_course_list(self):
        """创建新的课程列表"""
        name, ok1 = get_text_input(self, '新建课程列表', '请输入选课人名称:')
        if not ok1 or not name.strip():
            return
        
        text, ok2 = get_multiline_input(self, '新建课程列表', '请输入课程编号，每行一个:')
        if ok2 and text.strip():
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            
            # 读取/创建 courses.json
            courses_data = load_courses()
            courses_data[name] = lines
            save_courses(courses_data)
            
            StyledMessageBox.information(self, '已创建', f'已为 {name} 创建课程列表并保存到 courses.json')
            
            # 如果当前选中该用户，刷新显示
            if self.user_combo.currentText() == name:
                self.on_user_selected(name)
    
    def new_delete_course_list(self):
        """创建待删除课程列表"""
        name, ok1 = get_text_input(self, '待删除课程', '请输入选课人名称:')
        if not ok1 or not name.strip():
            return
        
        text, ok2 = get_multiline_input(self, '待删除课程', '请输入课程信息，每行格式：课程代码 班序\n例如：COMP101 1')
        if ok2 and text.strip():
            from core import load_delete_courses, save_delete_courses
            
            delete_courses = []
            for line in text.splitlines():
                line = line.strip()
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        course_code = parts[0]
                        class_no = parts[1]
                        delete_courses.append({
                            "courseCode": course_code,
                            "classNo": class_no
                        })
            
            if delete_courses:
                # 读取/创建 delete_courses.json
                delete_courses_data = load_delete_courses()
                delete_courses_data[name] = delete_courses
                save_delete_courses(delete_courses_data)
                
                StyledMessageBox.information(self, '已创建', f'已为 {name} 创建待删除课程列表，共 {len(delete_courses)} 门')
                
                # 如果当前选中该用户，刷新显示
                if self.user_combo.currentText() == name:
                    self.on_user_selected(name)
            else:
                StyledMessageBox.warning(self, '错误', '输入格式错误，请按 "课程代码 班序" 的格式输入')
    
    def new_account_dialog(self):
        """创建新账户"""
        from dialogs import get_account_input
        
        name, username, password, ok = get_account_input(self, '新建选课人')
        if not ok or not (name and username and password):
            return
        
        try:
            # 读取并追加 accounts.json
            accounts = load_accounts()
            
            # 检查是否已存在
            if any(acc['name'] == name for acc in accounts):
                StyledMessageBox.warning(self, '错误', f'选课人 {name} 已存在！')
                return
            
            accounts.append({
                'name': name,
                'username': username,
                'password': password
            })
            save_accounts(accounts)
            self.user_combo.addItem(name)
            
            # 同时在 cookies.json 和 courses.json 中创建占位符
            cookies_data = load_cookies_dict()
            cookies_data[name] = ""
            save_cookies_dict(cookies_data)
            
            courses_data = load_courses()
            if name not in courses_data:
                courses_data[name] = []
            save_courses(courses_data)
            
            StyledMessageBox.information(self, '已创建', f'已添加选课人: {name}')
        except Exception as e:
            StyledMessageBox.warning(self, '错误', f'无法保存账户: {e}')
    
    def update_cookie_for_user(self):
        """更新用户的 Cookie - 通过登录获取"""
        selected_user = self.user_combo.currentText()
        if not selected_user:
            StyledMessageBox.warning(self, "错误", "请先选择一个抢课人！")
            return
        
        # 获取选中用户的账户信息
        try:
            accounts = load_accounts()
            user_acc = next((acc for acc in accounts if acc["name"] == selected_user), None)
            if not user_acc:
                StyledMessageBox.warning(self, "错误", f"未找到用户 {selected_user} 的账户信息！")
                return
            
            username = user_acc["username"]
            password = user_acc["password"]
        except Exception as e:
            StyledMessageBox.warning(self, "错误", f"无法读取账户信息: {e}")
            return
        
        # 显示正在登录的提示
        self.status_box.append(f"正在为 {selected_user} 获取 Cookie...")
        
        try:
            # 调用 get_cookies 获取 cookies
            from core import get_cookies
            # 将 GUI 的状态写入函数作为回调传入，使得登录过程的进度可以显示在状态框中
            self.status_box.append("开始调用 get_cookies 函数...")
            cookies = get_cookies(username, password, report_callback=self.status_box.append)
            
            self.status_box.append(f"[调试] 获得的 cookies 对象类型: {type(cookies)}")
            self.status_box.append(f"[调试] 获得的 cookies 数量: {len(cookies)}")
            
            # 转换为字符串格式
            try:
                self.status_box.append("开始转换 cookies 为字符串格式...")
                cookies_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
                self.status_box.append(f"[调试] 转换成功，cookies 字符串长度: {len(cookies_str)}")
            except Exception as convert_error:
                self.status_box.append(f"❌ Cookies 转换失败: {convert_error}")
                raise
            
            # 保存到 cookies.json
            try:
                self.status_box.append("开始保存 cookies 到 cookies.json...")
                cookies_dict = load_cookies_dict()
                cookies_dict[selected_user] = cookies_str
                save_cookies_dict(cookies_dict)
                self.status_box.append("✓ Cookies 已保存到文件")
            except Exception as save_error:
                self.status_box.append(f"❌ Cookies 保存失败: {save_error}")
                raise
            
            self.status_box.append(f"✓ 已成功获取 {selected_user} 的 Cookie")
            StyledMessageBox.information(self, '已更新', f'已为 {selected_user} 成功获取并保存 Cookie')
            self.on_user_selected(selected_user)
        except Exception as e:
            import traceback
            self.status_box.append(f"✗ 获取 Cookie 失败: {e}")
            self.status_box.append(f"错误详情: {traceback.format_exc()}")
            StyledMessageBox.warning(self, '错误', f'无法获取 Cookie: {e}')
    
    def toggle_selection(self):
        """切换开始/停止选课"""
        if self.start_button.text() == "开始选课":
            self.start_selection()
        else:
            self.stop_selection()
    
    def start_selection(self):
        """开始选课"""
        selected_user = self.user_combo.currentText()
        if not selected_user or selected_user == "":
            StyledMessageBox.warning(self, "错误", "请从下拉菜单选择一个抢课人！")
            return
        
        # 从 accounts.json 读取用户信息
        try:
            accounts = load_accounts()
        except Exception:
            StyledMessageBox.warning(self, "错误", "未找到 accounts.json 文件！")
            return
        
        selected_acc = next((acc for acc in accounts if acc["name"] == selected_user), None)
        if not selected_acc:
            StyledMessageBox.warning(self, "错误", f"未找到选定的抢课人 {selected_user}！")
            return
        
        username = selected_acc["username"]
        password = selected_acc["password"]
        
        # 从 courses.json 读取该用户的课程列表
        try:
            courses_data = load_courses()
        except Exception:
            StyledMessageBox.warning(self, "错误", "未找到 courses.json 文件！")
            return
        
        courses = courses_data.get(selected_user, [])
        if not courses:
            StyledMessageBox.warning(
                self, 
                "错误", 
                f"用户 {selected_user} 在 courses.json 中没有课程列表！"
            )
            return
        
        # 从 cookies.json 读取该用户的 cookies
        try:
            cookies_dict = load_cookies_dict()
        except Exception:
            StyledMessageBox.warning(self, "错误", "未找到 cookies.json 文件！")
            return
        
        cookies_str = cookies_dict.get(selected_user, "")
        if not cookies_str:
            self.update_status(f"用户 {selected_user} 的 cookie 为空，需要更新。")
        
        self.thread = CourseSelectionThread(cookies_str, courses, username, password, selected_user, self.request_interval)
        self.thread.update_status.connect(self.update_status)
        self.thread.refresh_courses.connect(self.on_user_selected)  # 连接课程刷新信号
        self.thread.start()
        
        # 改变按钮为停止状态
        self.start_button.setText("停止选课")
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #BF616A;
                color: #2E3440;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #D17B7B;
            }}
            QPushButton:pressed {{
                background-color: #A53860;
            }}
        """)
    
    def stop_selection(self):
        """停止选课"""
        if self.thread:
            self.thread.stop()  # 调用线程的停止方法
            self.thread.wait()  # 等待线程完全停止
            self.update_status("✗ 已停止选课")
        
        # 恢复按钮为开始状态
        self.start_button.setText("开始选课")
        self.start_button.setStyleSheet(f"""
            QPushButton {{
                background-color: #A3BE8C;
                color: #2E3440;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #B8D896;
            }}
            QPushButton:pressed {{
                background-color: #95B475;
            }}
        """)
    
    def show_settings(self):
        """显示设置对话框"""
        from dialogs import get_settings_input
        
        new_interval, ok = get_settings_input(self, self.request_interval, '设置')
        if ok:
            self.request_interval = new_interval
            self.update_status(f"✓ 已更新请求间隔为 {self.request_interval} 秒")
    
    def update_status(self, message):
        """更新状态显示"""
        self.status_box.append(message)


def main():
    """应用入口"""
    # 解析运行时资源路径（兼容 PyInstaller 打包后的 _MEIPASS）
    def resource_path(relative_path: str) -> str:
        if getattr(sys, 'frozen', False):
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(__file__), relative_path)

    app = QApplication([])
    # 尝试加载图标并设置为应用/窗口图标（影响任务栏和窗口标题栏）
    try:
        icon_path = resource_path('logo.ico')
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            app.setWindowIcon(app_icon)
        else:
            # 若未找到 ico，仍尝试使用 png
            png_path = resource_path('logo.png')
            if os.path.exists(png_path):
                app_icon = QIcon(png_path)
                app.setWindowIcon(app_icon)
    except Exception:
        pass
    window = MainWindow()
    # Ensure main window also has the same icon (some platforms require this)
    try:
        if 'app_icon' in locals():
            window.setWindowIcon(app_icon)
    except Exception:
        pass
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
