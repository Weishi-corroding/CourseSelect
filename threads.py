# -*- coding: utf-8 -*-
"""后台线程处理模块"""

from PyQt5.QtCore import QThread, pyqtSignal
from core import get_cookies, sccourse


class CourseSelectionThread(QThread):
    """课程选择后台线程"""
    update_status = pyqtSignal(str)

    def __init__(self, cookies, courses, username, password, request_interval=2):
        super().__init__()
        self.cookies = cookies
        self.courses = courses
        self.username = username
        self.password = password
        self.request_interval = request_interval
        self.is_running = True  # 用于控制线程停止

    def run(self):
        """执行选课循环"""
        b = True
        while b and self.is_running:  # 添加 is_running 检查
            for courseid in self.courses:
                # 检查是否需要停止
                if not self.is_running:
                    break

                self.update_status.emit(f"正在选课, 课程ID: {courseid}...")

                # 调用 sccourse，并对可能的异常/错误返回做保护
                try:
                    result = sccourse(self.cookies, courseid)
                except Exception as e:
                    self.update_status.emit(f"调用选课接口异常: {e}")
                    result = f"EXCEPTION: {e}"

                # 如果线程在发起请求后被要求停止，尽早退出
                if not self.is_running:
                    break

                # 如果 sccourse 返回的是错误前缀，记录并继续
                if isinstance(result, str) and (result.startswith("CALL_ERROR") or result.startswith("TIMEOUT") or result.startswith("EXCEPTION")):
                    self.update_status.emit(f"选课请求出错: {result}")
                else:
                    # 正常响应判断选课成功的关键字
                    if "true" in result and "Empty" not in result:
                        self.update_status.emit(f"课程 {courseid} 选课成功！")
                        b = False
                        break
                    elif "F" in result:
                        self.update_status.emit("Cookie 可能已过期，需要重新登录。")
                        cookies = get_cookies(self.username, self.password, report_callback=self.update_status.emit)
                        self.cookies = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
                        self.update_status.emit("已更新 Cookie，重新尝试选课...")
                    else:
                        self.update_status.emit(f"课程 {courseid} 选课失败，返回信息: {result}")

                # 使用分段 sleep 以便在等待期间能快速响应停止请求
                total_ms = int(self.request_interval * 1000)
                slept = 0
                step = 200
                while slept < total_ms and self.is_running:
                    self.msleep(min(step, total_ms - slept))
                    slept += min(step, total_ms - slept)
    
    def stop(self):
        """停止线程"""
        self.is_running = False
