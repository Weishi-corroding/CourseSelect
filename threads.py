# -*- coding: utf-8 -*-
"""后台线程处理模块"""

from PyQt5.QtCore import QThread, pyqtSignal
from core import get_cookies, sccourse, load_courses, save_courses


class CourseSelectionThread(QThread):
    """课程选择后台线程"""
    update_status = pyqtSignal(str)
    refresh_courses = pyqtSignal(str)  # 信号：课程列表更新时，传入用户名

    def __init__(self, cookies, courses, username, password, user_display_name, request_interval=2):
        super().__init__()
        self.cookies = cookies
        self.courses = courses
        self.username = username
        self.password = password
        self.user_display_name = user_display_name  # GUI中显示的用户名
        self.request_interval = request_interval
        self.is_running = True  # 用于控制线程停止

    def run(self):
        """执行选课循环"""
        # 记录已成功选上的课程
        successful_courses = set()
        
        while self.is_running:
            for courseid in self.courses:
                # 检查是否需要停止
                if not self.is_running:
                    break

                # 如果这门课已经选成功过了，跳过
                if courseid in successful_courses:
                    self.update_status.emit(f"课程 {courseid} 已成功选课，跳过...")
                    continue

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
                        self.update_status.emit(f"✓ 课程 {courseid} 选课成功！")
                        successful_courses.add(courseid)
                        
                        # 从courses.json中移除已成功的课程
                        try:
                            courses_data = load_courses()
                            if self.user_display_name in courses_data:
                                updated_courses = [c for c in courses_data[self.user_display_name] if c != courseid]
                                courses_data[self.user_display_name] = updated_courses
                                save_courses(courses_data)
                                self.update_status.emit(f"已从待选列表中移除课程 {courseid}")
                                # 发送信号刷新 GUI 中的课程显示
                                self.refresh_courses.emit(self.user_display_name)
                        except Exception as e:
                            self.update_status.emit(f"⚠️  更新课程文件失败: {e}")
                        
                        # 如果所有课程都选成功了，停止循环
                        if len(successful_courses) == len(self.courses):
                            self.update_status.emit(f"✓ 所有课程（共 {len(self.courses)} 门）选课完成！")
                            self.is_running = False
                            break
                        # 否则继续选下一门课
                        continue
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
            
            # 检查是否所有课程都已成功选上
            if len(successful_courses) == len(self.courses):
                break
    
    def stop(self):
        """停止线程"""
        self.is_running = False
