# -*- coding: utf-8 -*-
"""主程序 - 应用入口"""

import sys
import os
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

# 导入生产版本的 Glassmorphism UI
from modern_ui_production import ProductionGlassmorphismUI

LOG_FILE = "CoureseSelectDebug.log"

def get_log_path():
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, LOG_FILE)

class TimestampLogger(object):
    """为标准输出添加时间戳的包装类"""
    def __init__(self, original_stream, prefix="[SYS]"):
        self.original_stream = original_stream
        self.prefix = prefix
        self.log_path = get_log_path()

    def write(self, message):
        # 避免空行重复打印时间戳
        if message.strip():
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            formatted_msg = f"[{timestamp}] {self.prefix} {message}\n"
            
            # 写文件
            try:
                with open(self.log_path, "a", encoding="utf-8") as f:
                    f.write(formatted_msg)
            except: pass
            
            # 同时也写回原始流（如果在控制台运行能看到）
            try:
                self.original_stream.write(formatted_msg)
                self.original_stream.flush()
            except: pass

    def flush(self):
        try:
            self.original_stream.flush()
        except: pass

def excepthook(exc_type, exc_value, exc_traceback):
    """全局异常捕获钩子"""
    import traceback
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    log_content = f"\n[{timestamp}] [CRASH] !!! GLOBAL EXCEPTION !!!\n{error_msg}\n"
    
    try:
        with open(get_log_path(), "a", encoding="utf-8") as f:
            f.write(log_content)
    except: pass
    
    print(error_msg)

# 设置全局异常钩子
sys.excepthook = excepthook

# 重定向 stdout 和 stderr
sys.stdout = TimestampLogger(sys.stdout, "[INFO]")
sys.stderr = TimestampLogger(sys.stderr, "[ERR ]")

print("程序启动，日志系统已初始化...")

def main():
    """应用入口"""
    def resource_path(relative_path: str) -> str:
        if getattr(sys, 'frozen', False):
            return os.path.join(sys._MEIPASS, relative_path)
        return os.path.join(os.path.dirname(__file__), relative_path)

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 尝试加载应用图标
    try:
        icon_path = resource_path('logo.ico')
        if os.path.exists(icon_path):
            app_icon = QIcon(icon_path)
            app.setWindowIcon(app_icon)
    except Exception:
        pass
    
    # 创建并显示生产版本 Glassmorphism UI
    try:
        window = ProductionGlassmorphismUI()
        window.show()
        print("主窗口已显示")
        app.exec_()
    except Exception as e:
        print(f"主循环异常: {e}")

if __name__ == "__main__":
    main()
