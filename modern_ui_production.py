# -*- coding: utf-8 -*-
"""
最终修正版：Windows 11 Glassmorphism UI
功能升级：无限轮次 + 多线程并发 + 统一日志 + 定时启动 + 浏览器选择 + 微信推送
"""

import sys
import os
import json
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QGridLayout, QFrame, QTabWidget, QMessageBox, QFileDialog, 
    QMenuBar, QMenu, QListWidget, QDialog, QSizePolicy, QInputDialog
)
from PyQt5.QtGui import QFont, QColor, QCursor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMutex, QMutexLocker, QTimer, QTime

# 导入 core
from core import (
    load_accounts, save_accounts, load_courses, save_courses,
    load_cookies_dict, save_cookies_dict, load_delete_courses, save_delete_courses,
    get_cookies, sccourse, cancelSC, send_push_notification
)

file_lock = QMutex()

class SingleCourseWorker(QThread):
    """单门课程抢课线程"""
    log_signal = pyqtSignal(str)
    success_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, cookies, course_id, user_display_name, interval=0.5, push_token=""):
        super().__init__()
        self.cookies = cookies
        self.course_id = course_id
        self.user_display_name = user_display_name
        self.interval = interval
        self.push_token = push_token
        self.is_running = True
        self.retry_count = 0

    def run(self):
        self.log_signal.emit(f"🔥 线程启动: 目标课程 [{self.course_id}]")
        while self.is_running:
            try:
                result = sccourse(self.cookies, self.course_id)
                self.retry_count += 1
                result_str = str(result)
                
                if "true" in result_str or "成功" in result_str or "已选" in result_str:
                    msg = f"✅ [{self.course_id}] 抢课成功！(第{self.retry_count}次)"
                    self.log_signal.emit(msg)
                    self.success_signal.emit(self.course_id)
                    
                    if self.push_token:
                        self.log_signal.emit("📲 正在发送微信推送...")
                        send_push_notification(
                            self.push_token, 
                            "🎉 抢课成功通知", 
                            f"恭喜！用户 {self.user_display_name} 成功抢到课程：<b>{self.course_id}</b><br>尝试次数：{self.retry_count}"
                        )

                    self.remove_course_from_json()
                    break
                elif "Full" in result_str or "满" in result_str:
                    if self.retry_count % 10 == 0:
                        self.log_signal.emit(f"⏳ [{self.course_id}] 人数已满，继续重试... ({self.retry_count})")
                elif "TIMEOUT" in result_str:
                    self.log_signal.emit(f"⚠️ [{self.course_id}] 请求超时")
                else:
                    if len(result_str) > 50: result_str = result_str[:50] + "..."
                    self.log_signal.emit(f"📝 [{self.course_id}] 结果: {result_str}")
            except Exception as e:
                self.log_signal.emit(f"❌ [{self.course_id}] 线程异常: {e}")
            
            if self.interval > 0:
                self.msleep(int(self.interval * 1000))
        
        self.log_signal.emit(f"🛑 线程停止: [{self.course_id}]")
        self.finished_signal.emit(self.course_id)

    def remove_course_from_json(self):
        locker = QMutexLocker(file_lock)
        try:
            d = load_courses()
            if self.user_display_name in d:
                original_len = len(d[self.user_display_name])
                d[self.user_display_name] = [c for c in d[self.user_display_name] if c != self.course_id]
                if len(d[self.user_display_name]) < original_len:
                    save_courses(d)
        except Exception as e:
            self.log_signal.emit(f"⚠️ 文件写入错误: {e}")

    def stop(self):
        self.is_running = False

class PreWorkThread(QThread):
    """预处理线程"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, cookies, delete_list, interval=1):
        super().__init__()
        self.cookies = cookies
        self.delete_list = delete_list
        self.interval = interval

    def run(self):
        if self.delete_list:
            self.log_signal.emit(f"{'='*40}\n📌 开始处理待删除课程 ({len(self.delete_list)}门)")
            for item in self.delete_list:
                cc = item.get("courseCode", "")
                cn = item.get("classNo", "")
                self.log_signal.emit(f"⏳ 正在删除: {cc} (班序: {cn})")
                try:
                    res = cancelSC(self.cookies, cc, cn)
                    self.log_signal.emit(f"  📝 结果: {res}")
                except Exception as e:
                    self.log_signal.emit(f"  ⚠️ 异常: {e}")
                self.msleep(int(self.interval * 1000))
            self.log_signal.emit(f"✅ 退课处理完成\n{'='*40}")
        self.finished_signal.emit()

class StyledInputDialog(QDialog):
    """改进的输入对话框"""
    def __init__(self, parent, title, prompt, is_multiline=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(450, 200)
        self.dark_mode = getattr(parent, 'dark_mode', False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        title_label = QLabel(prompt)
        title_label.setFont(QFont("Microsoft YaHei UI", 12))
        layout.addWidget(title_label)
        
        if is_multiline:
            self.input_field = QTextEdit()
            self.input_field.setMinimumHeight(120)
        else:
            self.input_field = QLineEdit()
            self.input_field.setMinimumHeight(35)
        
        self.input_field.setFont(QFont("Microsoft YaHei UI", 11))
        layout.addWidget(self.input_field)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        self.apply_style()
    
    def apply_style(self):
        if self.dark_mode:
            self.setStyleSheet("""
                QDialog { background-color: #202040; color: white; }
                QLabel { color: white; }
                QLineEdit, QTextEdit { background: rgba(255,255,255,0.1); color: white; border: 1px solid #555; }
                QPushButton { background: #0072FF; color: white; border-radius: 5px; padding: 5px 15px; }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background-color: #F5F7FA; color: black; }
                QLabel { color: black; }
                QLineEdit, QTextEdit { background: white; color: black; border: 1px solid #CCC; }
                QPushButton { background: #3B82F6; color: white; border-radius: 5px; padding: 5px 15px; }
            """)

    def get_value(self):
        return self.input_field.toPlainText() if isinstance(self.input_field, QTextEdit) else self.input_field.text()

class ProductionGlassmorphismUI(QMainWindow):
    """主界面类"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("🎓 智能抢课系统 Pro (并发版)")
        self.setGeometry(50, 50, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        self.workers = [] 
        self.pre_work_thread = None
        self.is_running = False
        self.request_interval = 0.5 
        self.dark_mode = True 
        
        # === 核心配置 ===
        self.scheduled_time = None 
        self.browser_type = "edge" 
        self.push_token = "" 
        
        self.load_settings() # 加载设置（浏览器类型、Push Token等）

        self.schedule_timer = QTimer(self)
        self.schedule_timer.timeout.connect(self.check_schedule)
        self.schedule_timer.start(1000) 
        
        self.create_menu_bar()
        self.create_central_ui()
        self.apply_glassmorphism_style()
        self.load_initial_data()
    
    def load_settings(self):
        try:
            if os.path.exists("settings.json"):
                with open("settings.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.push_token = data.get("push_token", "")
        except: pass

    def save_settings(self):
        try:
            # 读取现有文件以免覆盖其他设置（如果有）
            data = {}
            if os.path.exists("settings.json"):
                with open("settings.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["push_token"] = self.push_token
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except: pass

    def create_menu_bar(self):
        menubar = self.menuBar()
        menubar.setFont(QFont("Microsoft YaHei UI", 12))
        
        file_menu = menubar.addMenu("📁 文件")
        file_menu.addAction("导入配置目录").triggered.connect(self.import_config_directory)
        file_menu.addSeparator()
        file_menu.addAction("退出").triggered.connect(self.close)
        
        edit_menu = menubar.addMenu("✏️ 编辑")
        edit_menu.addAction("添加待选课程").triggered.connect(self.add_new_course)
        edit_menu.addAction("添加待删除课程").triggered.connect(self.add_delete_course)
        edit_menu.addSeparator()
        edit_menu.addAction("新建选课人").triggered.connect(self.new_account_dialog)
        
        settings_menu = menubar.addMenu("⚙️ 设置")
        settings_menu.addAction("更新 Cookie").triggered.connect(self.update_cookie_dialog)
        settings_menu.addSeparator()
        settings_menu.addAction("并发间隔").triggered.connect(self.set_request_interval)
        settings_menu.addAction("设置定时启动").triggered.connect(self.set_schedule_dialog)
        settings_menu.addAction("切换浏览器引擎").triggered.connect(self.select_browser_dialog)
        settings_menu.addAction("配置微信推送").triggered.connect(self.set_push_token_dialog)
        settings_menu.addSeparator()
        self.theme_action = settings_menu.addAction("🌙 切换为浅色模式")
        self.theme_action.triggered.connect(self.toggle_theme)
    
    def create_central_ui(self):
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)
        
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        self.title_label = QLabel("⚡ 智能抢课系统 Pro (并发版)")
        self.title_label.setFont(QFont("Microsoft YaHei UI", 24, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.title_label)
        
        main_layout.addWidget(self._create_user_section())
        
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Microsoft YaHei UI", 12))
        self.tabs.addTab(self._create_courses_tab(), "📋 课程管理")
        self.tabs.addTab(self._create_logs_tab(), "📊 系统日志")
        main_layout.addWidget(self.tabs, 1)
        
        self.start_stop_button = QPushButton("🚀 开始并发选课")
        self.start_stop_button.setFont(QFont("Microsoft YaHei UI", 16, QFont.Bold))
        self.start_stop_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.start_stop_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_stop_button.setMinimumHeight(60)
        self.start_stop_button.clicked.connect(self.toggle_selection)
        main_layout.addWidget(self.start_stop_button)
    
    def _create_user_section(self):
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        label = QLabel("选择抢课人:")
        label.setFont(QFont("Microsoft YaHei UI", 14, QFont.Bold))
        
        self.user_combo = QComboBox()
        self.user_combo.setFont(QFont("Microsoft YaHei UI", 12))
        self.user_combo.setMinimumHeight(40)
        self.user_combo.currentTextChanged.connect(self.on_user_changed)
        
        self.user_info_label = QLabel("")
        self.user_info_label.setFont(QFont("Microsoft YaHei UI", 11))
        
        layout.addWidget(label)
        layout.addWidget(self.user_combo, 2)
        layout.addWidget(self.user_info_label, 2)
        layout.addStretch()
        return frame
    
    def _create_courses_tab(self):
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(20)
        
        left_frame = QFrame()
        left_layout = QVBoxLayout(left_frame)
        left_layout.addWidget(QLabel("📌 待选课程 (每门课一个线程)"))
        self.course_list = QListWidget()
        self.course_list.setFont(QFont("Microsoft YaHei UI", 12))
        left_layout.addWidget(self.course_list)
        layout.addWidget(left_frame, 0, 0)
        
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.addWidget(QLabel("🗑️ 待删除课程 (启动前优先执行)"))
        self.delete_course_list = QListWidget()
        self.delete_course_list.setFont(QFont("Microsoft YaHei UI", 12))
        right_layout.addWidget(self.delete_course_list)
        layout.addWidget(right_frame, 0, 1)
        return widget
    
    def _create_logs_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 12))
        layout.addWidget(self.log_display)
        return widget

    def apply_glassmorphism_style(self):
        if self.dark_mode:
            colors = {
                'bg_start': '#202040', 'bg_mid': '#1a1a2e', 'bg_end': '#202060',
                'text_main': '#FFFFFF', 'card_bg': 'rgba(255, 255, 255, 0.08)',
                'card_border': 'rgba(255, 255, 255, 0.15)', 'input_bg': 'rgba(0, 0, 0, 0.2)',
                'menu_bg': '#202040', 'menu_hover': 'rgba(0, 198, 255, 0.2)',
                'list_item_bg': 'rgba(255, 255, 255, 0.05)', 'list_item_sel': 'rgba(0, 198, 255, 0.3)',
                'btn_bg_1': '#4B0082', 'btn_bg_2': '#483D8B', 'btn_hover': '#6A5ACD'
            }
        else:
            colors = {
                'bg_start': '#F0F3F9', 'bg_mid': '#E6EAF0', 'bg_end': '#DCE4F0',
                'text_main': '#202020', 'card_bg': 'rgba(255, 255, 255, 0.75)',
                'card_border': 'rgba(0, 0, 0, 0.08)', 'input_bg': '#FFFFFF',
                'menu_bg': '#F9FAFB', 'menu_hover': 'rgba(59, 130, 246, 0.1)',
                'list_item_bg': '#FFFFFF', 'list_item_sel': 'rgba(59, 130, 246, 0.2)',
                'btn_bg_1': '#3B82F6', 'btn_bg_2': '#2563EB', 'btn_hover': '#60A5FA'
            }

        if self.is_running:
            btn_style = """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #FF4444, stop:1 #CC0000);
                color: #FFFFFF; border: none; border-radius: 12px; font-weight: bold;
            }
            QPushButton:hover { background-color: #FF6666; }
            """
        else:
            btn_style = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {colors['btn_bg_1']}, stop:1 {colors['btn_bg_2']});
                color: #FFFFFF; border: none; border-radius: 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {colors['btn_hover']}; }}
            """

        qss = f"""
        QMainWindow#MainWindow {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {colors['bg_start']}, stop:0.5 {colors['bg_mid']}, stop:1 {colors['bg_end']});
        }}
        QWidget#CentralWidget {{ background: transparent; }}
        QWidget {{ color: {colors['text_main']}; font-family: "Microsoft YaHei UI", sans-serif; }}
        QFrame {{ background-color: {colors['card_bg']}; border: 1px solid {colors['card_border']}; border-radius: 12px; }}
        QMenuBar {{ background-color: {colors['menu_bg']}; border-bottom: 1px solid {colors['card_border']}; }}
        QMenuBar::item {{ background: transparent; padding: 5px 10px; }}
        QMenuBar::item:selected {{ background-color: {colors['menu_hover']}; border-radius: 4px; }}
        QMenu {{ background-color: {colors['menu_bg']}; border: 1px solid {colors['card_border']}; padding: 5px; }}
        QMenu::item:selected {{ background-color: {colors['menu_hover']}; border-radius: 4px; }}
        QLineEdit, QTextEdit, QComboBox {{ background-color: {colors['input_bg']}; border: 1px solid {colors['card_border']}; border-radius: 6px; padding: 5px; selection-background-color: {colors['btn_bg_1']}; }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
        QListWidget {{ background-color: {colors['input_bg']}; border: 1px solid {colors['card_border']}; border-radius: 8px; outline: none; }}
        QListWidget::item {{ background-color: {colors['list_item_bg']}; border-radius: 6px; margin: 2px; padding: 8px; color: {colors['text_main']}; }}
        QListWidget::item:selected {{ background-color: {colors['list_item_sel']}; border: 1px solid {colors['btn_bg_1']}; }}
        QTabWidget::pane {{ border: none; background: transparent; }}
        QTabBar::tab {{ background: {colors['card_bg']}; color: {colors['text_main']}; padding: 8px 20px; margin-right: 4px; border-top-left-radius: 8px; border-top-right-radius: 8px; }}
        QTabBar::tab:selected {{ background: {colors['btn_bg_1']}; color: #FFFFFF; }}
        {btn_style}
        """
        self.setStyleSheet(qss)

    def load_initial_data(self):
        try:
            accounts = load_accounts()
            self.user_combo.blockSignals(True)
            self.user_combo.clear()
            self.user_combo.addItem("")
            for acc in accounts:
                self.user_combo.addItem(acc["name"])
            self.user_combo.blockSignals(False)
            self.log_display.append("✓ 系统就绪")
            self.log_display.append(f"✓ 当前浏览器引擎: {self.browser_type.upper()}")
        except: pass

    def on_user_changed(self, username):
        if not username: return
        try:
            accs = load_accounts()
            u = next((a for a in accs if a['name'] == username), None)
            if u: self.user_info_label.setText(f"ID: {u['username']}")
            
            c_data = load_courses()
            self.course_list.clear()
            for c in c_data.get(username, []):
                self.course_list.addItem(str(c))
            
            d_data = load_delete_courses()
            self.delete_course_list.clear()
            for c in d_data.get(username, []):
                self.delete_course_list.addItem(f"{c['courseCode']} (班序:{c['classNo']})")
        except: pass

    def import_config_directory(self):
        path = QFileDialog.getExistingDirectory(self, "选择配置目录")
        if not path: return
        self.log_display.append(f"导入目录: {path}")
        try:
            for fname in ['accounts.json', 'courses.json', 'cookies.json', 'delete_courses.json']:
                fpath = os.path.join(path, fname)
                if os.path.exists(fpath):
                    with open(fpath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if fname == 'accounts.json': save_accounts(data.get('accounts', data))
                    elif fname == 'courses.json': save_courses(data)
                    elif fname == 'cookies.json': save_cookies_dict(data)
                    elif fname == 'delete_courses.json': save_delete_courses(data)
                    self.log_display.append(f"✓ 已导入: {fname}")
            self.load_initial_data()
        except Exception as e:
            self.log_display.append(f"导入出错: {e}")

    def add_new_course(self):
        u = self.user_combo.currentText()
        if not u: return
        cid, ok = self._get_text_input("添加", "课程编号:")
        if ok and cid:
            try:
                d = load_courses()
                if u not in d: d[u] = []
                d[u].append(cid)
                save_courses(d)
                self.on_user_changed(u)
            except Exception as e: self.log_display.append(str(e))

    def add_delete_course(self):
        u = self.user_combo.currentText()
        if not u: return
        cc, ok1 = self._get_text_input("添加", "课程代码:")
        cn, ok2 = self._get_text_input("添加", "班序:")
        if ok1 and ok2:
            try:
                d = load_delete_courses()
                if u not in d: d[u] = []
                d[u].append({"courseCode": cc, "classNo": cn})
                save_delete_courses(d)
                self.on_user_changed(u)
            except Exception as e: self.log_display.append(str(e))

    def new_account_dialog(self):
        name, ok1 = self._get_text_input("新建", "名称:")
        uid, ok2 = self._get_text_input("新建", "学号:")
        pwd, ok3 = self._get_text_input("新建", "密码:")
        if ok1 and ok2 and ok3:
            try:
                accs = load_accounts()
                accs.append({'name': name, 'username': uid, 'password': pwd})
                save_accounts(accs)
                self.load_initial_data()
            except: pass
    
    # === 定时检测逻辑 ===
    def check_schedule(self):
        if self.scheduled_time and not self.is_running:
            current_time = QTime.currentTime().toString("HH:mm:ss")
            if current_time == self.scheduled_time:
                self.log_display.append(f"⏰ 触发定时任务: {current_time}")
                self.toggle_selection()
                self.scheduled_time = None 
                self.title_label.setText(f"⚡ 智能抢课系统 Pro (并发版)")

    def set_schedule_dialog(self):
        time_str, ok = self._get_text_input("定时启动", "输入启动时间 (HH:mm:ss):")
        if ok and time_str:
            if len(time_str.split(':')) == 3:
                self.scheduled_time = time_str
                self.log_display.append(f"⏰ 定时已设置: {self.scheduled_time}")
                self.title_label.setText(f"⚡ 智能抢课系统 Pro (定时: {self.scheduled_time})")
            else:
                QMessageBox.warning(self, "格式错误", "请使用 HH:mm:ss 格式，例如 12:59:59")

    def select_browser_dialog(self):
        items = ["System Edge (默认)", "Chrome Portable/System"]
        item, ok = QInputDialog.getItem(self, "选择浏览器", "请选择登录用的浏览器引擎:", items, 0, False)
        if ok and item:
            if "Chrome" in item:
                self.browser_type = "chrome"
            else:
                self.browser_type = "edge"
            self.log_display.append(f"🔧 浏览器引擎已切换为: {self.browser_type.upper()}")

    # === 新增：微信推送配置弹窗 ===
    def set_push_token_dialog(self):
        token, ok = self._get_text_input("微信推送配置", "请输入 PushPlus Token (留空则关闭):")
        if ok:
            self.push_token = token.strip()
            self.save_settings()
            if self.push_token:
                self.log_display.append(f"📲 推送 Token 已保存: {self.push_token[:4]}****")
                send_push_notification(self.push_token, "抢课系统测试", "您的 Token 配置成功！")
            else:
                self.log_display.append("📲 推送功能已关闭")

    def update_cookie_dialog(self):
        u = self.user_combo.currentText()
        if not u:
            QMessageBox.warning(self, "错误", "请先选择一个抢课人")
            return
        try:
            accs = load_accounts()
            user_account = next((a for a in accs if a['name'] == u), None)
            if not user_account:
                QMessageBox.warning(self, "错误", f"未找到用户 [{u}]")
                return
            
            browser_name = "Edge" if self.browser_type == "edge" else "Chrome"
            reply = QMessageBox.question(self, "准备就绪", 
                                       f"即将使用 [{browser_name}] 为 [{u}] 获取 Cookie。\n请确保浏览器可用。",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.No: return
            
            self.log_display.append(f"--- 正在获取 {u} 的 Cookie (引擎: {browser_name}) ---")
            
            cookies_list = get_cookies(
                user_account['username'], 
                user_account['password'], 
                report_callback=self.log_display.append,
                browser_type=self.browser_type
            )
            
            if cookies_list:
                cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])
                all_cookies = load_cookies_dict()
                all_cookies[u] = cookie_str
                save_cookies_dict(all_cookies)
                self.log_display.append(f"✅ {u} Cookie 保存成功！")
                QMessageBox.information(self, "成功", "Cookie 更新成功！")
            else:
                self.log_display.append("⚠️ Cookie 获取失败")
        except Exception as e:
            self.log_display.append(f"❌ 异常: {e}")

    def set_request_interval(self):
        s, ok = self._get_text_input("设置", "并发间隔(秒):")
        if ok:
            try:
                val = float(s)
                self.request_interval = val
            except: pass

    def toggle_selection(self):
        if not self.is_running:
            self.start_selection()
        else:
            self.stop_selection()

    def start_selection(self):
        u = self.user_combo.currentText()
        if not u: return
        self.is_running = True
        self.start_stop_button.setText("⏹️  停止并发抢课")
        self.apply_glassmorphism_style()
        self.tabs.setCurrentIndex(1)
        
        d_courses = load_delete_courses().get(u, [])
        cookies = load_cookies_dict().get(u, "")
        if not cookies:
            self.log_display.append("❌ 未找到Cookie，请先更新！")
            self.stop_selection()
            return

        self.pre_work_thread = PreWorkThread(cookies, d_courses)
        self.pre_work_thread.log_signal.connect(self.log_display.append)
        self.pre_work_thread.finished_signal.connect(lambda: self.launch_concurrent_workers(u, cookies))
        self.pre_work_thread.start()

    def launch_concurrent_workers(self, u, cookies):
        if not self.is_running: return
        courses = load_courses().get(u, [])
        if not courses:
            self.log_display.append("⚠️ 没有待选课程")
            self.stop_selection()
            return
        self.log_display.append(f"🚀 启动并发引擎: {len(courses)} 个线程并行处理...")
        self.workers = [] 
        for cid in courses:
            # === 传入 push_token ===
            worker = SingleCourseWorker(cookies, cid, u, self.request_interval, self.push_token)
            worker.log_signal.connect(self.log_display.append)
            worker.success_signal.connect(self.highlight_successful_courses)
            worker.finished_signal.connect(self.on_worker_finished)
            self.workers.append(worker)
            worker.start()
            QThread.msleep(100)

    def stop_selection(self):
        self.is_running = False
        self.log_display.append("⏹️ 正在停止所有线程...")
        if self.pre_work_thread and self.pre_work_thread.isRunning():
            self.pre_work_thread.terminate() 
        for w in self.workers:
            if w.isRunning():
                w.stop()
                w.wait() 
        self.workers.clear()
        self.start_stop_button.setText("🚀 开始并发选课")
        self.apply_glassmorphism_style()
        self.log_display.append("✅ 所有操作已停止")

    def on_worker_finished(self, course_id):
        pass

    def highlight_successful_courses(self, course_id):
        for i in range(self.course_list.count()):
            item = self.course_list.item(i)
            if item.text() == course_id:
                item.setBackground(QColor(0, 100, 50))
                item.setForeground(QColor(0, 255, 127))

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.theme_action.setText("🌙 切换为浅色模式" if self.dark_mode else "🌙 切换为深色模式")
        self.apply_glassmorphism_style()
        self.log_display.append("✓ 主题已切换")

    def _get_text_input(self, title, prompt, is_multiline=False):
        dialog = StyledInputDialog(self, title, prompt, is_multiline)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_value(), True
        return "", False
    
    def closeEvent(self, event):
        if self.is_running: self.stop_selection()
        event.accept()