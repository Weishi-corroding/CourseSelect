# -*- coding: utf-8 -*-
"""
最终修正版：Windows 11 Glassmorphism UI
功能升级：无限轮次 + 多线程并发 + 统一日志 + 定时启动 + 浏览器选择 + 微信推送 + 捡漏模式(完美模拟+交互修正)
"""
import os
import json
import random
import threading
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QGridLayout, QFrame, QTabWidget, QMessageBox, QFileDialog,
    QListWidget, QDialog, QSizePolicy, QInputDialog,
    QCheckBox, QScrollArea, QApplication
)
from PyQt5.QtGui import QFont, QColor, QCursor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMutex, QMutexLocker, QTimer, QTime

# 导入 core
from core import (
    load_accounts, save_accounts, load_courses, save_courses,
    load_cookies_dict, save_cookies_dict, load_delete_courses, save_delete_courses,
    get_cookies, sccourse, cancelSC, send_push_notification, 
    query_course_info, access_judge
)

file_lock = QMutex()

class SingleCourseWorker(QThread):
    """单门课程抢课线程 - 智能防风控版"""
    log_signal = pyqtSignal(str)
    success_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)
    captcha_signal = pyqtSignal()  # 验证码请求信号

    def __init__(self, cookies, course_id, user_display_name, interval=0.5, push_token=""):
        super().__init__()
        self.cookies = cookies
        self.course_id = course_id
        self.user_display_name = user_display_name
        self.interval = interval
        self.push_token = push_token
        self.is_running = True
        self.retry_count = 0
        self.empty_count = 0
        self.use_cap_code = False  # 下次请求是否携带验证码参数
        self.captcha_event = threading.Event()
        self.captcha_code = ""

    def run(self):
        self.log_signal.emit(f"🔥 线程启动: 目标课程 [{self.course_id}]")
        while self.is_running:
            try:
                # 检测到需验证码时，下次请求携带 capCode=1234 绕过
                cap = "1234" if self.use_cap_code else ""
                self.use_cap_code = False
                result = sccourse(self.cookies, self.course_id, cap)
                self.retry_count += 1
                result_str = str(result).strip()

                if not result_str:
                    self.handle_soft_ban("空响应")
                    continue

                try:
                    res_json = json.loads(result_str)
                    if res_json.get("msg") == "F" or res_json.get("capType") == "Empty":
                        # --- 验证码处理：弹窗请求用户输入 ---
                        self.log_signal.emit(f"⚠️ [{self.course_id}] 需要验证码，正在请求用户输入...")
                        self.captcha_code = ""
                        self.captcha_event.clear()
                        self.captcha_signal.emit()
                        if self.captcha_event.wait(timeout=120):
                            cap = self.captcha_code
                            self.captcha_code = ""
                            if cap:
                                self.log_signal.emit(f"📝 [{self.course_id}] 已获取验证码，重新提交...")
                                result = sccourse(self.cookies, self.course_id, cap)
                                self.retry_count += 1
                                result_str = str(result).strip()
                                if result_str:
                                    try:
                                        res_json = json.loads(result_str)
                                    except json.JSONDecodeError:
                                        pass
                                # fall through to normal result check below
                            else:
                                self.log_signal.emit(f"⚠️ [{self.course_id}] 验证码为空，跳过")
                                self.msleep(1000)
                                continue
                        else:
                            self.log_signal.emit(f"⚠️ [{self.course_id}] 验证码输入超时(120s)，继续轮询")
                            self.msleep(1000)
                            continue
                    is_success = res_json.get("success") is True and res_json.get("msg") != "F"
                    if not isinstance(res_json, dict):
                        is_success = "true" in str(res_json).lower()
                except json.JSONDecodeError:
                    is_success = "true" in result_str and "Empty" not in result_str and "F" not in result_str

                if is_success:
                    self.handle_success()
                    break 
                elif "Full" in result_str or "满" in result_str:
                    if self.retry_count % 10 == 0:
                        self.log_signal.emit(f"⏳ [{self.course_id}] 人数已满..., 尝试 (第{self.retry_count}次)")
                elif "TIMEOUT" in result_str:
                    self.log_signal.emit(f"⚠️ [{self.course_id}] 请求超时")
                else:
                    if self.retry_count % 5 == 0:
                        self.log_signal.emit(f"📝 [{self.course_id}] 结果: {result_str[:60]}...")
            except Exception as e:
                self.log_signal.emit(f"❌ [{self.course_id}] 线程异常: {e}")
            
            if self.interval > 0:
                jitter = random.uniform(0, self.interval * 0.6)
                self.msleep(int((self.interval + jitter) * 1000))
        self.finished_signal.emit(self.course_id)

    def handle_soft_ban(self, reason):
        self.empty_count += 1
        if self.empty_count >= 3:
            sleep_time = random.uniform(10, 20) 
            self.log_signal.emit(f"🛑 [{self.course_id}] 检测到{reason}，强制避让 {sleep_time:.1f}秒...")
            self.msleep(int(sleep_time * 1000))
            self.empty_count = 0
        else:
            self.log_signal.emit(f"⚠️ [{self.course_id}] {reason}，慢速重试...")
            self.msleep(2000) 

    def handle_success(self):
        msg = f"✅ [{self.course_id}] 抢课成功！(第{self.retry_count}次)"
        self.log_signal.emit(msg)
        self.success_signal.emit(self.course_id)
        if self.push_token:
            from core import send_push_notification
            send_push_notification(self.push_token, "🎉 抢课成功通知", f"恭喜！{self.user_display_name} 抢到：{self.course_id}")
        self.remove_course_from_json()

    def remove_course_from_json(self):
        locker = QMutexLocker(file_lock)
        try:
            d = load_courses()
            if self.user_display_name in d:
                original_len = len(d[self.user_display_name])
                d[self.user_display_name] = [c for c in d[self.user_display_name] if c != self.course_id]
                if len(d[self.user_display_name]) < original_len:
                    save_courses(d)
        except: pass
    def stop(self): self.is_running = False


# === 捡漏模式工作线程 (修复版) ===
class PickUpWorker(QThread):
    """捡漏模式线程：完全模拟 [权限检查 -> 查询] 循环"""
    log_signal = pyqtSignal(str)
    success_signal = pyqtSignal(str)
    captcha_signal = pyqtSignal()

    def __init__(self, cookies, course_code, target_ctt_ids, user_name, interval=1.0, push_token=""):
        super().__init__()
        self.cookies = cookies
        self.course_code = course_code
        self.target_ctt_ids = target_ctt_ids
        self.user_name = user_name
        self.interval = interval
        self.push_token = push_token
        self.is_running = True
        self.check_count = 0
        self.use_cap_code = False
        self.captcha_event = threading.Event()
        self.captcha_code = ""

    def run(self):
        self.log_signal.emit(f"🕵️‍♂️ 捡漏模式启动: 监控课程代码 [{self.course_code}]")
        self.log_signal.emit(f"🎯 包含目标班级(cttId): {self.target_ctt_ids}")
        
        while self.is_running:
            try:
                # === 步骤 1: 权限检查 (accessJudge) ===
                # 每次循环都执行，完全模拟点击行为
                # self.log_signal.emit("Checking access...") # 日志太多可注释
                judge_res = access_judge(self.cookies, self.course_code)
                
                # 如果鉴权失败（比如被登出、风控、或返回 false），则不进行下一步查询
                if '"success":true' not in str(judge_res):
                    self.log_signal.emit(f"⚠️ 权限检查未通过: {str(judge_res)}... (可能已失效或被拦截)")
                    self.msleep(5000) # 冷却一下
                    continue 

                # === 模拟人类操作的微小延迟 ===
                # 浏览器发完 accessJudge 后加载 initACC 肯定有几十毫秒的间隔
                self.msleep(random.randint(200, 500))

                # === 步骤 2: 获取列表 (initACC) ===
                res_str = query_course_info(self.cookies, self.course_code)
                self.check_count += 1
                
                # 解析数据
                try:
                    data = json.loads(res_str)
                    if not data.get("success"):
                         self.log_signal.emit(f"⚠️ 查询失败: {data.get('msg', '未知错误')}")
                    else:
                        class_list = data.get("aaData", [])
                        found_target = False
                        
                        for cls in class_list:
                            ctt_id = str(cls.get("cttId"))
                            
                            if ctt_id in self.target_ctt_ids:
                                found_target = True
                                max_cnt = int(cls.get("maxCnt", 0))
                                enroll_cnt = int(cls.get("enrollCnt", 0))
                                class_no = cls.get("classNo", "?")
                                course_name = cls.get("crName", "未知课程")
                                
                                remaining = max_cnt - enroll_cnt
                                
                                # === 步骤 3: 发现空位 -> 抢课 ===
                                if remaining > 0:
                                    self.log_signal.emit(f"⚡ 发现空位！[{course_name}] 班级[{class_no}] 余量: {remaining}")
                                    self.log_signal.emit(f"🚀 立即发起抢课请求 -> {ctt_id}")

                                    cap = "1234" if self.use_cap_code else ""
                                    self.use_cap_code = False
                                    sc_res = sccourse(self.cookies, ctt_id, cap)

                                    # 检测是否需要验证码
                                    try:
                                        sc_json = json.loads(sc_res)
                                        if sc_json.get("msg") == "F":
                                            # --- 验证码处理：弹窗请求用户输入 ---
                                            self.log_signal.emit("⚠️ 抢课遇到验证码，正在请求用户输入...")
                                            self.captcha_code = ""
                                            self.captcha_event.clear()
                                            self.captcha_signal.emit()
                                            if self.captcha_event.wait(timeout=120):
                                                real_cap = self.captcha_code
                                                self.captcha_code = ""
                                                if real_cap:
                                                    self.log_signal.emit(f"📝 已获取验证码，重新提交...")
                                                    sc_res = sccourse(self.cookies, ctt_id, real_cap)
                                                    # fall through to result check below
                                                else:
                                                    self.log_signal.emit("⚠️ 验证码为空，跳过")
                                                    self.msleep(1000)
                                                    continue
                                            else:
                                                self.log_signal.emit("⚠️ 验证码输入超时(120s)，继续监控")
                                                self.msleep(1000)
                                                continue
                                    except:
                                        pass

                                    if "true" in str(sc_res) or "成功" in str(sc_res):
                                        self.handle_success(ctt_id, class_no, course_name)
                                    else:
                                        self.log_signal.emit(f"❌ 抢课失败: {sc_res}")
                                else:
                                    if self.check_count % 20 == 0:
                                        self.log_signal.emit(f"👀 ({self.check_count})监控中... [{course_name}][{class_no}] 满员 ({enroll_cnt}/{max_cnt})")

                        if not found_target and self.check_count % 10 == 0:
                             self.log_signal.emit(f"⚠️ 警告: 未找到目标ID。请确认CourseCode {self.course_code} 正确。")

                except json.JSONDecodeError:
                    if not res_str:
                         self.log_signal.emit("⚠️ 查询返回为空 (可能被限流)，冷却中...")
                         self.msleep(5000)
                    else:
                         self.log_signal.emit(f"⚠️ 解析JSON失败")

            except Exception as e:
                self.log_signal.emit(f"❌ 捡漏线程异常: {e}")
            
            # 循环间隔 (包含随机抖动)
            if self.interval > 0:
                jitter = random.uniform(0, self.interval * 0.5)
                self.msleep(int((self.interval + jitter) * 1000))
        
        self.log_signal.emit(f"⏹️ 捡漏监控停止: {self.course_code}")

    def handle_success(self, ctt_id, class_no, course_name):
        msg = f"🎉 捡漏成功！{course_name} (班级:{class_no})"
        self.log_signal.emit(msg)
        self.success_signal.emit(ctt_id)
        
        if self.push_token:
            from core import send_push_notification
            send_push_notification(self.push_token, "捡漏成功通知", msg)
            
        if ctt_id in self.target_ctt_ids:
            self.target_ctt_ids.remove(ctt_id)
            self.remove_course_from_json(ctt_id)
            
        if not self.target_ctt_ids:
            self.log_signal.emit("✅ 所有目标班级已搞定，停止监控。")
            self.stop()

    def remove_course_from_json(self, ctt_id):
        locker = QMutexLocker(file_lock)
        try:
            d = load_courses()
            if self.user_name in d:
                original_len = len(d[self.user_name])
                d[self.user_name] = [c for c in d[self.user_name] if c != ctt_id]
                if len(d[self.user_name]) < original_len:
                    save_courses(d)
        except: pass

    def stop(self):
        self.is_running = False


# === 升级课程线程 ===
class UpgradeWorker(QThread):
    """
    升级课程：监控目标课程，发现空位时先退掉旧课、再选新课。
    流程：initACC(kcbh_target) → 发现空位 →
          cancelSC(kcbh_current, classNo_current) → sccourse(cttId_target)
    注意：不使用 accessJudge，因为已选课程会使其返回失败。
    """
    log_signal = pyqtSignal(str)
    success_signal = pyqtSignal(str)  # "当前课程 → 目标课程"
    finished_signal = pyqtSignal()
    captcha_signal = pyqtSignal()

    def __init__(self, cookies, user_name, current_ctt_id, target_ctt_id, interval=1.0, push_token=""):
        super().__init__()
        self.cookies = cookies
        self.user_name = user_name
        self.current_ctt_id = str(current_ctt_id)
        self.target_ctt_id = str(target_ctt_id)
        self.interval = interval
        self.push_token = push_token
        self.is_running = True
        self.check_count = 0
        self.use_cap_code = False
        self.captcha_event = threading.Event()
        self.captcha_code = ""
        self._course_data = None  # 缓存 courses_full.json

    def _load_course_data(self):
        """加载 courses_full.json 并缓存"""
        if self._course_data is not None:
            return self._course_data
        path = getattr(getattr(self, 'parent', None), 'PICKUP_DATA_FILE', "courses_full.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._course_data = json.load(f)
        except:
            self._course_data = {}
        return self._course_data

    def _lookup_kcbh(self, ctt_id):
        """cttId → {kcbh, kcmc, classNo, maxCnt, enrollCnt}"""
        data = self._load_course_data()
        for course in data.get("courses", []):
            kcbh = course.get("kcbh", "")
            kcmc = course.get("kcmc", "")
            tt = course.get("timetable")
            if not tt:
                continue
            for cls in tt.get("classes", []):
                if cls.get("cttId") == ctt_id:
                    return {
                        "kcbh": kcbh,
                        "kcmc": kcmc,
                        "classNo": cls.get("classNo", ""),
                        "maxCnt": cls.get("maxCnt", 0),
                        "enrollCnt": cls.get("enrollCnt", 0),
                    }
        return None

    def run(self):
        # ── 1. 查找信息 ──
        current_info = self._lookup_kcbh(self.current_ctt_id)
        target_info = self._lookup_kcbh(self.target_ctt_id)

        if not target_info:
            self.log_signal.emit(f"❌ 未在 courses_full.json 中找到目标课程 (cttId={self.target_ctt_id})")
            self.finished_signal.emit()
            return

        current_name = current_info["kcmc"] if current_info else self.current_ctt_id
        target_name = target_info["kcmc"]
        target_kcbh = target_info["kcbh"]

        self.log_signal.emit(f"🆙 升级线程启动: [{current_name}] → [{target_name}]")
        if current_info:
            self.log_signal.emit(f"  当前: {current_info['kcbh']} 班序{current_info['classNo']} "
                                 f"({current_info['enrollCnt']}/{current_info['maxCnt']})")
        self.log_signal.emit(f"  目标: {target_kcbh} ({target_info['enrollCnt']}/{target_info['maxCnt']})")
        self.log_signal.emit("⏳ 等待目标课程出现空位...")

        while self.is_running:
            try:
                # ── 直接查询班级列表（不用 accessJudge，已选课程会使它失败）──
                self.msleep(random.randint(200, 500))
                res_str = query_course_info(self.cookies, target_kcbh)
                self.check_count += 1

                try:
                    data = json.loads(res_str)
                except json.JSONDecodeError:
                    if not res_str and self.check_count % 5 == 0:
                        self.log_signal.emit("⚠️ 查询返回为空，可能被限流")
                    self.msleep(5000)
                    continue

                if not data.get("success"):
                    if self.check_count % 5 == 0:
                        self.log_signal.emit(f"⚠️ 查询失败: {data.get('msg', '未知')}")
                    self.msleep(3000)
                    continue

                # ── 查找目标班级 ──
                found_vacancy = False
                for cls in data.get("aaData", []):
                    if str(cls.get("cttId")) == self.target_ctt_id:
                        enroll = int(cls.get("enrollCnt", 0))
                        max_cnt = int(cls.get("maxCnt", 0))
                        remaining = max_cnt - enroll

                        if remaining > 0:
                            found_vacancy = True
                            class_no = cls.get("classNo", "?")
                            self.log_signal.emit(f"⚡ 发现空位！[{target_name}] 班级[{class_no}] "
                                                 f"余量: {remaining}/{max_cnt}")

                            # ── 步骤 A: 退掉当前课程 ──
                            if current_info:
                                cancel_res = cancelSC(self.cookies,
                                                      current_info["kcbh"],
                                                      current_info["classNo"])
                                self.log_signal.emit(f"📝 退课结果: {cancel_res}")
                                # 简单判断退课是否成功
                                if '"success":true' not in str(cancel_res) and "成功" not in str(cancel_res):
                                    self.log_signal.emit("⚠️ 退课可能失败，仍尝试选课...")

                            # ── 步骤 B: 选择目标课程 ──
                            self.log_signal.emit(f"🚀 发起选课请求 -> {self.target_ctt_id}")
                            cap = "1234" if self.use_cap_code else ""
                            self.use_cap_code = False
                            sc_res = sccourse(self.cookies, self.target_ctt_id, cap)

                            # 检测是否需要验证码
                            try:
                                sc_json = json.loads(sc_res)
                                if sc_json.get("msg") == "F":
                                    # --- 验证码处理：弹窗请求用户输入 ---
                                    self.log_signal.emit("⚠️ 选课遇到验证码，正在请求用户输入...")
                                    self.captcha_code = ""
                                    self.captcha_event.clear()
                                    self.captcha_signal.emit()
                                    if self.captcha_event.wait(timeout=120):
                                        real_cap = self.captcha_code
                                        self.captcha_code = ""
                                        if real_cap:
                                            self.log_signal.emit(f"📝 已获取验证码，重新提交...")
                                            sc_res = sccourse(self.cookies, self.target_ctt_id, real_cap)
                                            # fall through to result check below
                                        else:
                                            self.log_signal.emit("⚠️ 验证码为空，跳过")
                                            self.msleep(1000)
                                            continue
                                    else:
                                        self.log_signal.emit("⚠️ 验证码输入超时(120s)，继续监控")
                                        self.msleep(1000)
                                        continue
                            except:
                                pass

                            if "true" in str(sc_res) or "成功" in str(sc_res):
                                msg = f"🎉 升级成功！{current_name} → {target_name}"
                                self.log_signal.emit(msg)
                                self.success_signal.emit(f"{self.current_ctt_id}→{self.target_ctt_id}")
                                if self.push_token:
                                    send_push_notification(self.push_token, "🆙 升级课程成功", msg)
                                self.is_running = False
                                self.finished_signal.emit()
                                return
                            else:
                                self.log_signal.emit(f"❌ 选课失败: {sc_res}")
                                self.log_signal.emit("💡 目标可能已被抢走，继续等待新空位...")

                        else:
                            if self.check_count % 15 == 0:
                                self.log_signal.emit(f"👀 ({self.check_count}) 监控中... "
                                                     f"[{target_name}] 满员 ({enroll}/{max_cnt})")

                if not found_vacancy and self.check_count % 10 == 0:
                    self.log_signal.emit(f"👀 ({self.check_count}) 目标课程无空位，继续监控...")

            except Exception as e:
                self.log_signal.emit(f"❌ 升级线程异常: {e}")
                import traceback
                self.log_signal.emit(traceback.format_exc())

            # 循环间隔 + 随机抖动
            if self.interval > 0 and self.is_running:
                jitter = random.uniform(0, self.interval * 0.5)
                self.msleep(int((self.interval + jitter) * 1000))

        self.log_signal.emit("⏹️ 升级监控已停止")
        self.finished_signal.emit()

    def stop(self):
        self.is_running = False

class PreWorkThread(QThread):
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
                QDialog {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #202040, stop:0.5 #1a1a2e, stop:1 #202060);
                    color: white;
                }
                QLabel { color: white; font-size: 13px; }
                QLineEdit, QTextEdit {
                    background: rgba(255,255,255,0.1);
                    color: white;
                    border: 1px solid rgba(255,255,255,0.15);
                    border-radius: 6px;
                    padding: 6px 10px;
                    font-size: 13px;
                }
                QLineEdit:focus, QTextEdit:focus {
                    border: 1px solid #6A5ACD;
                }
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #4B0082, stop:1 #483D8B);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background: #6A5ACD;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #F0F3F9, stop:0.5 #E6EAF0, stop:1 #DCE4F0);
                    color: #202020;
                }
                QLabel { color: #202020; font-size: 13px; }
                QLineEdit, QTextEdit {
                    background: white;
                    color: #202020;
                    border: 1px solid rgba(0,0,0,0.12);
                    border-radius: 6px;
                    padding: 6px 10px;
                    font-size: 13px;
                }
                QLineEdit:focus, QTextEdit:focus {
                    border: 1px solid #3B82F6;
                }
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #3B82F6, stop:1 #2563EB);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background: #2563EB;
                }
            """)
    def get_value(self):
        return self.input_field.toPlainText() if isinstance(self.input_field, QTextEdit) else self.input_field.text()


class CaptchaDialog(QDialog):
    """验证码输入弹窗 - 从服务器获取验证码图片并让用户输入"""
    def __init__(self, parent, cookies, caption=""):
        super().__init__(parent)
        self.setWindowTitle("验证码输入")
        self.setMinimumSize(420, 320)
        self.cookies = cookies
        self.dark_mode = getattr(parent, 'dark_mode', False)
        self._cap_code = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        prompt = QLabel("请输入验证码：" + (f" ({caption})" if caption else ""))
        prompt.setFont(QFont("Microsoft YaHei UI", 12))
        prompt.setAlignment(Qt.AlignCenter)
        layout.addWidget(prompt)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setMinimumHeight(90)
        self.image_label.setStyleSheet("border: 1px solid #888; border-radius: 6px; padding: 8px;")
        layout.addWidget(self.image_label)

        refresh_btn = QPushButton("🔄 刷新验证码")
        refresh_btn.setFont(QFont("Microsoft YaHei UI", 11))
        refresh_btn.setCursor(QCursor(Qt.PointingHandCursor))
        refresh_btn.clicked.connect(self._fetch_captcha_image)
        layout.addWidget(refresh_btn)

        self.input_field = QLineEdit()
        self.input_field.setMinimumHeight(38)
        self.input_field.setFont(QFont("Microsoft YaHei UI", 16))
        self.input_field.setAlignment(Qt.AlignCenter)
        self.input_field.setPlaceholderText("输入图片中的验证码")
        layout.addWidget(self.input_field)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("✔ 确定")
        ok_btn.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        ok_btn.setMinimumSize(100, 36)
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("✖ 取消")
        cancel_btn.setFont(QFont("Microsoft YaHei UI", 12))
        cancel_btn.setMinimumSize(100, 36)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.input_field.returnPressed.connect(self.accept)
        self._fetch_captcha_image()
        self._apply_style()

    def _parse_cookies(self):
        cookies = {}
        for item in self.cookies.split(";"):
            item = item.strip()
            if "=" in item:
                k, v = item.split("=", 1)
                cookies[k.strip()] = v.strip()
        return cookies

    def _fetch_captcha_image(self):
        self.image_label.setText("⏳ 加载验证码中...")
        QThread.msleep(50)
        QApplication.processEvents()
        try:
            import requests
            headers = {
                "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) "
                               "Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"),
                "Referer": "https://jwgl.dhu.edu.cn/dhu/selectcourse/toSH",
            }
            resp = requests.get(
                "https://jwgl.dhu.edu.cn/dhu/captcha/code",
                headers=headers,
                cookies=self._parse_cookies(),
                timeout=15
            )
            if resp.status_code == 200:
                pixmap = QPixmap()
                if pixmap.loadFromData(resp.content):
                    scaled = pixmap.scaledToHeight(80, Qt.SmoothTransformation)
                    self.image_label.setPixmap(scaled)
                else:
                    self.image_label.setText("⚠️ 图片解析失败，点击刷新重试")
            else:
                self.image_label.setText(f"⚠️ 请求失败 (HTTP {resp.status_code})")
        except Exception as e:
            self.image_label.setText(f"❌ 加载失败: {e}")

    def get_value(self):
        return self.input_field.text().strip()

    def _apply_style(self):
        if self.dark_mode:
            self.setStyleSheet("""
                QDialog { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #202040, stop:0.5 #1a1a2e, stop:1 #202060); color: white; }
                QLabel { color: white; font-size: 13px; }
                QLineEdit {
                    background: rgba(255,255,255,0.1); color: white;
                    border: 2px solid rgba(255,255,255,0.2); border-radius: 8px;
                    padding: 6px 10px; font-size: 16px;
                }
                QLineEdit:focus { border: 2px solid #6A5ACD; }
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #4B0082, stop:1 #483D8B);
                    color: white; border: none; border-radius: 6px;
                    padding: 8px 16px; font-weight: bold;
                }
                QPushButton:hover { background: #6A5ACD; }
            """)
        else:
            self.setStyleSheet("""
                QDialog { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #F0F3F9, stop:0.5 #E6EAF0, stop:1 #DCE4F0); color: #202020; }
                QLabel { color: #202020; font-size: 13px; }
                QLineEdit {
                    background: white; color: #202020;
                    border: 2px solid rgba(0,0,0,0.15); border-radius: 8px;
                    padding: 6px 10px; font-size: 16px;
                }
                QLineEdit:focus { border: 2px solid #3B82F6; }
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #3B82F6, stop:1 #2563EB);
                    color: white; border: none; border-radius: 6px;
                    padding: 8px 16px; font-weight: bold;
                }
                QPushButton:hover { background: #2563EB; }
            """)


# === 多选账号弹窗 ===
class SelectAccountsDialog(QDialog):
    """显示所有账号，用复选框选择需要更新 Cookie 的目标"""
    def __init__(self, parent, accounts):
        super().__init__(parent)
        self.setWindowTitle("选择要更新 Cookie 的账号")
        self.setMinimumSize(480, 350)
        self.dark_mode = getattr(parent, 'dark_mode', False)
        self.setObjectName("SelectAccountsDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 标题
        title = QLabel("请勾选需要更新 Cookie 的账号：")
        title.setFont(QFont("Microsoft YaHei UI", 13))
        layout.addWidget(title)

        # 全选 / 取消全选
        self.select_all_cb = QCheckBox("全选 / 取消全选")
        self.select_all_cb.setFont(QFont("Microsoft YaHei UI", 11))
        self.select_all_cb.stateChanged.connect(self._on_select_all)
        layout.addWidget(self.select_all_cb)

        # 账号复选框列表
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll_container = QWidget()
        self.checkbox_layout = QVBoxLayout(scroll_container)
        self.checkbox_layout.setContentsMargins(0, 0, 0, 0)
        self.checkbox_layout.setSpacing(6)

        self.account_checkboxes = []
        # 读取已有 cookie 信息
        cookies_dict = load_cookies_dict()
        for acc in accounts:
            name = acc["name"]
            uid = acc["username"]
            has_cookie = "✅" if cookies_dict.get(name) else "❌"
            cb = QCheckBox(f"{has_cookie}  {name}  (ID: {uid})")
            cb.setFont(QFont("Microsoft YaHei UI", 11))
            cb.setChecked(False)
            cb.acc_info = acc  # 挂载账号信息
            self.checkbox_layout.addWidget(cb)
            self.account_checkboxes.append(cb)

        self.checkbox_layout.addStretch()
        scroll.setWidget(scroll_container)
        layout.addWidget(scroll, 1)

        # 底部统计 + 按钮
        info_layout = QHBoxLayout()
        self.count_label = QLabel(f"已选择 0 / {len(accounts)} 个账号")
        self.count_label.setFont(QFont("Microsoft YaHei UI", 11))
        info_layout.addWidget(self.count_label)
        info_layout.addStretch()

        ok_btn = QPushButton("确定更新")
        ok_btn.setObjectName("DialogOkBtn")
        ok_btn.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        ok_btn.setMinimumSize(120, 38)
        ok_btn.clicked.connect(self.accept)
        info_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("DialogCancelBtn")
        cancel_btn.setFont(QFont("Microsoft YaHei UI", 12))
        cancel_btn.setMinimumSize(80, 38)
        cancel_btn.clicked.connect(self.reject)
        info_layout.addWidget(cancel_btn)

        layout.addLayout(info_layout)

        # 监听复选框变化以更新计数
        for cb in self.account_checkboxes:
            cb.stateChanged.connect(self._update_count)
        self._update_count()
        self._apply_style()

    def _on_select_all(self, state):
        checked = state == Qt.Checked
        for cb in self.account_checkboxes:
            cb.setChecked(checked)

    def _update_count(self):
        selected = sum(1 for cb in self.account_checkboxes if cb.isChecked())
        total = len(self.account_checkboxes)
        self.count_label.setText(f"已选择 {selected} / {total} 个账号")

    def get_selected_accounts(self):
        return [cb.acc_info for cb in self.account_checkboxes if cb.isChecked()]

    def _apply_style(self):
        if self.dark_mode:
            self.setStyleSheet("""
                QDialog#SelectAccountsDialog {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #202040, stop:0.5 #1a1a2e, stop:1 #202060);
                    color: white;
                }
                QLabel { color: white; }
                QCheckBox {
                    color: white; spacing: 10px;
                    padding: 6px 8px;
                    border-radius: 6px;
                }
                QCheckBox:hover {
                    background: rgba(255,255,255,0.08);
                }
                QCheckBox::indicator {
                    width: 20px; height: 20px;
                    border: 2px solid rgba(255,255,255,0.3);
                    border-radius: 4px;
                    background: transparent;
                }
                QCheckBox::indicator:checked {
                    background: #4B0082;
                    border-color: #6A5ACD;
                }
                QCheckBox::indicator:hover {
                    border-color: rgba(255,255,255,0.6);
                }
                QScrollArea { border: none; background: transparent; }
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #4B0082, stop:1 #483D8B);
                    color: white; border: none; border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton:hover { background: #6A5ACD; }
                QPushButton#DialogCancelBtn {
                    background: rgba(255,255,255,0.1);
                }
                QPushButton#DialogCancelBtn:hover {
                    background: rgba(255,255,255,0.2);
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog#SelectAccountsDialog {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #F0F3F9, stop:0.5 #E6EAF0, stop:1 #DCE4F0);
                    color: #202020;
                }
                QLabel { color: #202020; }
                QCheckBox {
                    color: #202020; spacing: 10px;
                    padding: 6px 8px;
                    border-radius: 6px;
                }
                QCheckBox:hover {
                    background: rgba(0,0,0,0.03);
                }
                QCheckBox::indicator {
                    width: 20px; height: 20px;
                    border: 2px solid rgba(0,0,0,0.2);
                    border-radius: 4px;
                    background: white;
                }
                QCheckBox::indicator:checked {
                    background: #3B82F6;
                    border-color: #2563EB;
                }
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #3B82F6, stop:1 #2563EB);
                    color: white; border: none; border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton:hover { background: #2563EB; }
                QPushButton#DialogCancelBtn {
                    background: rgba(0,0,0,0.08);
                }
                QPushButton#DialogCancelBtn:hover {
                    background: rgba(0,0,0,0.15);
                }
            """)

# === 课程多选弹窗（捡漏模式） ===
class SelectCoursesDialog(QDialog):
    """显示所有待抢课程（按课程代码分组），复选框选择要捡漏的目标"""
    def __init__(self, parent, kcbh_groups, unknown_ctt=None):
        super().__init__(parent)
        self.setWindowTitle("选择要捡漏的课程")
        self.setMinimumSize(520, 400)
        self.dark_mode = getattr(parent, 'dark_mode', False)
        self.setObjectName("SelectCoursesDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("请勾选需要启动捡漏监控的课程（默认全选）：")
        title.setFont(QFont("Microsoft YaHei UI", 13))
        layout.addWidget(title)

        # 全选 / 取消全选
        self.select_all_cb = QCheckBox("全选 / 取消全选")
        self.select_all_cb.setFont(QFont("Microsoft YaHei UI", 11))
        self.select_all_cb.setChecked(True)
        self.select_all_cb.stateChanged.connect(self._on_select_all)
        layout.addWidget(self.select_all_cb)

        # 课程复选框列表（滚动区域）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        container = QWidget()
        self.cb_layout = QVBoxLayout(container)
        self.cb_layout.setContentsMargins(0, 0, 0, 0)
        self.cb_layout.setSpacing(6)

        self.course_checkboxes = []  # 每个元素: (checkbox, kcbh, cttIds列表)
        # 按 kcbh 排序显示
        for kcbh in sorted(kcbh_groups.keys()):
            group = kcbh_groups[kcbh]
            kcmc = group["kcmc"]
            ctt_ids = group["cttIds"]
            label = f"📘 {kcbh} {kcmc}  ({len(ctt_ids)} 个班级)"
            cb = QCheckBox(label)
            cb.setFont(QFont("Microsoft YaHei UI", 11))
            cb.setChecked(True)
            cb.kcbh = kcbh
            cb.ctt_ids = ctt_ids
            cb.kcmc = kcmc
            self.cb_layout.addWidget(cb)
            self.course_checkboxes.append(cb)

        # 未匹配的课程（不在 courses_full.json 中的 cttId）
        if unknown_ctt:
            sep = QLabel("⚠️ 以下课程未在数据文件中找到（仍可通过代码监控）：")
            sep.setFont(QFont("Microsoft YaHei UI", 10))
            sep.setStyleSheet("color: #FFA500; padding: 4px 0;")
            self.cb_layout.addWidget(sep)
            for ctt_id in unknown_ctt:
                cb = QCheckBox(f"❓ 未知课程 (cttId={ctt_id})")
                cb.setFont(QFont("Microsoft YaHei UI", 11))
                cb.setChecked(True)
                cb.kcbh = ctt_id   # 直接用 cttId 作为 kcbh
                cb.ctt_ids = [ctt_id]
                cb.kcmc = ctt_id
                self.cb_layout.addWidget(cb)
                self.course_checkboxes.append(cb)

        self.cb_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll, 1)

        # 底部统计 + 按钮
        info_layout = QHBoxLayout()
        self.count_label = QLabel(f"已选择 {len(self.course_checkboxes)} / {len(self.course_checkboxes)} 门课程")
        self.count_label.setFont(QFont("Microsoft YaHei UI", 11))
        info_layout.addWidget(self.count_label)
        info_layout.addStretch()

        ok_btn = QPushButton("启动捡漏")
        ok_btn.setObjectName("DialogOkBtn")
        ok_btn.setFont(QFont("Microsoft YaHei UI", 12, QFont.Bold))
        ok_btn.setMinimumSize(120, 38)
        ok_btn.clicked.connect(self.accept)
        info_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setObjectName("DialogCancelBtn")
        cancel_btn.setFont(QFont("Microsoft YaHei UI", 12))
        cancel_btn.setMinimumSize(80, 38)
        cancel_btn.clicked.connect(self.reject)
        info_layout.addWidget(cancel_btn)

        layout.addLayout(info_layout)

        for cb in self.course_checkboxes:
            cb.stateChanged.connect(self._update_count)
        self._update_count()
        self._apply_style()

    def _on_select_all(self, state):
        checked = state == Qt.Checked
        for cb in self.course_checkboxes:
            cb.setChecked(checked)

    def _update_count(self):
        selected = sum(1 for cb in self.course_checkboxes if cb.isChecked())
        total = len(self.course_checkboxes)
        self.count_label.setText(f"已选择 {selected} / {total} 门课程")

    def get_selected_groups(self):
        """返回 {kcbh: {"cttIds": [...], "kcmc": "..."}}"""
        groups = {}
        for cb in self.course_checkboxes:
            if cb.isChecked():
                groups[cb.kcbh] = {"cttIds": cb.ctt_ids, "kcmc": cb.kcmc}
        return groups

    def _apply_style(self):
        if self.dark_mode:
            self.setStyleSheet("""
                QDialog#SelectCoursesDialog {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #202040, stop:0.5 #1a1a2e, stop:1 #202060);
                    color: white;
                }
                QLabel { color: white; }
                QCheckBox {
                    color: white; spacing: 10px;
                    padding: 6px 8px; border-radius: 6px;
                }
                QCheckBox:hover { background: rgba(255,255,255,0.08); }
                QCheckBox::indicator {
                    width: 20px; height: 20px;
                    border: 2px solid rgba(255,255,255,0.3);
                    border-radius: 4px; background: transparent;
                }
                QCheckBox::indicator:checked {
                    background: #4B0082; border-color: #6A5ACD;
                }
                QCheckBox::indicator:hover { border-color: rgba(255,255,255,0.6); }
                QScrollArea { border: none; background: transparent; }
                QPushButton#DialogOkBtn {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #4B0082, stop:1 #483D8B);
                    color: white; border: none; border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton#DialogOkBtn:hover { background: #6A5ACD; }
                QPushButton#DialogCancelBtn {
                    background: rgba(255,255,255,0.1);
                }
                QPushButton#DialogCancelBtn:hover { background: rgba(255,255,255,0.2); }
            """)
        else:
            self.setStyleSheet("""
                QDialog#SelectCoursesDialog {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #F0F3F9, stop:0.5 #E6EAF0, stop:1 #DCE4F0);
                    color: #202020;
                }
                QLabel { color: #202020; }
                QCheckBox {
                    color: #202020; spacing: 10px;
                    padding: 6px 8px; border-radius: 6px;
                }
                QCheckBox:hover { background: rgba(0,0,0,0.03); }
                QCheckBox::indicator {
                    width: 20px; height: 20px;
                    border: 2px solid rgba(0,0,0,0.2);
                    border-radius: 4px; background: white;
                }
                QCheckBox::indicator:checked {
                    background: #3B82F6; border-color: #2563EB;
                }
                QScrollArea { border: none; background: transparent; }
                QPushButton#DialogOkBtn {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #3B82F6, stop:1 #2563EB);
                    color: white; border: none; border-radius: 6px;
                    padding: 8px 16px;
                }
                QPushButton#DialogOkBtn:hover { background: #2563EB; }
                QPushButton#DialogCancelBtn {
                    background: rgba(0,0,0,0.08);
                }
                QPushButton#DialogCancelBtn:hover { background: rgba(0,0,0,0.15); }
            """)

class ProductionGlassmorphismUI(QMainWindow):
    """主界面类"""
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("🎓 智能抢课系统 Pro (并发版)")
        self.setGeometry(50, 50, 1200, 800)
        self.setMinimumSize(1000, 700)
        
        self.workers = []
        self.pickup_workers = []
        self.upgrade_workers = []
        self.pre_work_thread = None
        self.is_running = False
        self.request_interval = 1.0
        self.dark_mode = True 
        
        self.scheduled_time = None 
        self.browser_type = "edge" 
        self.push_token = "" 
        
        self.load_settings()

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
        
        settings_menu.addAction("🔥 启动捡漏模式").triggered.connect(self.start_pickup_mode_dialog)
        settings_menu.addAction("🆙 升级课程").triggered.connect(self.upgrade_course_dialog)

        settings_menu.addAction("并发/查询间隔").triggered.connect(self.set_request_interval)
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
                'btn_bg_1': '#3B82F6', 'btn_bg_2': '#2563EB', 'btn_hover': '#6A5ACD'
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
        QComboBox QAbstractItemView {{
            background-color: {colors['menu_bg']};
            color: {colors['text_main']};
            selection-background-color: {colors['btn_bg_1']};
            selection-color: #FFFFFF;
            border: 1px solid {colors['card_border']};
            outline: none;
        }}
        QListWidget {{ background-color: {colors['input_bg']}; border: 1px solid {colors['card_border']}; border-radius: 8px; outline: none; }}
        QListWidget::item {{ background-color: {colors['list_item_bg']}; border-radius: 6px; margin: 2px; padding: 8px; color: {colors['text_main']}; }}
        QListWidget::item:selected {{ background-color: {colors['list_item_sel']}; border: 1px solid {colors['btn_bg_1']}; }}
        QTabWidget::pane {{ border: none; background: transparent; }}
        QTabBar::tab {{ background: {colors['card_bg']}; color: {colors['text_main']}; padding: 8px 20px; margin-right: 4px; border-top-left-radius: 8px; border-top-right-radius: 8px; }}
        QTabBar::tab:selected {{ background: {colors['btn_bg_1']}; color: #FFFFFF; }}
        QMessageBox {{
            background-color: {colors['bg_mid']};
            color: {colors['text_main']};
        }}
        QMessageBox QLabel {{
            color: {colors['text_main']};
            font-size: 13px;
        }}
        QMessageBox QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {colors['btn_bg_1']}, stop:1 {colors['btn_bg_2']});
            color: #FFFFFF;
            border: none;
            border-radius: 6px;
            padding: 8px 24px;
            font-weight: bold;
            min-width: 80px;
            min-height: 30px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {colors['btn_hover']};
        }}
        QInputDialog {{
            background-color: {colors['bg_mid']};
            color: {colors['text_main']};
        }}
        QInputDialog QLabel {{
            color: {colors['text_main']};
            font-size: 13px;
        }}
        QInputDialog QLineEdit {{
            background-color: {colors['input_bg']};
            color: {colors['text_main']};
            border: 1px solid {colors['card_border']};
            border-radius: 6px;
            padding: 6px 10px;
            font-size: 13px;
        }}
        QInputDialog QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {colors['btn_bg_1']}, stop:1 {colors['btn_bg_2']});
            color: #FFFFFF;
            border: none;
            border-radius: 6px;
            padding: 8px 24px;
            font-weight: bold;
            min-width: 80px;
            min-height: 30px;
        }}
        QInputDialog QPushButton:hover {{
            background-color: {colors['btn_hover']};
        }}
        QInputDialog QComboBox {{
            background-color: {colors['input_bg']};
            color: {colors['text_main']};
            border: 1px solid {colors['card_border']};
            border-radius: 6px;
            padding: 4px 8px;
        }}
        QInputDialog QComboBox::drop-down {{ border: none; width: 20px; }}
        QInputDialog QComboBox QAbstractItemView {{
            background-color: {colors['input_bg']};
            color: {colors['text_main']};
            selection-background-color: {colors['btn_bg_1']};
        }}
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

    def set_push_token_dialog(self):
        token, ok = self._get_text_input("微信推送配置", "请输入 PushPlus Token (留空则关闭):")
        if ok:
            self.push_token = token.strip()
            self.save_settings()
            if self.push_token:
                self.log_display.append(f"📲 推送 Token 已保存: {self.push_token[:4]}****")
                from core import send_push_notification
                send_push_notification(self.push_token, "抢课系统测试", "您的 Token 配置成功！")
            else:
                self.log_display.append("📲 推送功能已关闭")

    def update_cookie_dialog(self):
        """弹出账号多选窗口，为选中的账号依次获取 Cookie"""
        accounts = load_accounts()
        if not accounts:
            QMessageBox.warning(self, "错误", "没有账号数据，请先新建选课人")
            return

        dialog = SelectAccountsDialog(self, accounts)
        if dialog.exec_() != QDialog.Accepted:
            return

        selected = dialog.get_selected_accounts()
        if not selected:
            QMessageBox.information(self, "提示", "未选择任何账号")
            return

        browser_name = "Edge" if self.browser_type == "edge" else "Chrome"
        self.log_display.append(f"--- 开始批量获取 Cookie (引擎: {browser_name}) ---")
        self.log_display.append(f"📋 共 {len(selected)} 个账号需要更新")

        success_count = 0
        fail_count = 0
        all_cookies = load_cookies_dict()

        for i, acc in enumerate(selected, 1):
            name = acc["name"]
            uid = acc["username"]
            pwd = acc["password"]

            self.log_display.append(f"\n[{i}/{len(selected)}] 正在处理: {name} ({uid})")

            # 每个账号启动前都确认一次（浏览器弹窗需要人工交互）
            reply = QMessageBox.question(
                self, f"准备就绪 — {name}",
                f"即将使用 [{browser_name}] 为 [{name}] 获取 Cookie。\n"
                f"请确保浏览器可用，并手动完成验证码（如有）。\n\n"
                f"进度: {i}/{len(selected)}",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                self.log_display.append(f"⏭️ 已跳过: {name}")
                continue

            try:
                cookies_list = get_cookies(
                    uid, pwd,
                    report_callback=self.log_display.append,
                    browser_type=self.browser_type
                )
                if cookies_list:
                    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])
                    all_cookies[name] = cookie_str
                    save_cookies_dict(all_cookies)
                    self.log_display.append(f"✅ [{name}] Cookie 保存成功！")
                    success_count += 1
                else:
                    self.log_display.append(f"⚠️ [{name}] Cookie 获取失败（返回为空）")
                    fail_count += 1
            except Exception as e:
                self.log_display.append(f"❌ [{name}] 异常: {e}")
                fail_count += 1

        # 汇总
        self.log_display.append(f"\n{'='*40}")
        self.log_display.append(f"📊 批量更新完成: 成功 {success_count}，失败 {fail_count}，共 {len(selected)}")
        if fail_count == 0 and success_count > 0:
            QMessageBox.information(self, "完成", f"全部 {success_count} 个账号 Cookie 更新成功！")
        elif fail_count > 0:
            QMessageBox.warning(self, "完成", f"成功 {success_count} 个，失败 {fail_count} 个。请查看日志。")

    def set_request_interval(self):
        s, ok = self._get_text_input("设置", "并发间隔(秒):")
        if ok:
            try:
                val = float(s)
                self.request_interval = val
            except: pass

    # === 关键修正: 统一的启动/停止逻辑 ===
    def toggle_selection(self):
        # 如果正在运行（无论是普通抢课还是捡漏监控），都调用停止
        if self.is_running or self.pickup_workers:
            self.stop_selection()
        else:
            self.start_selection()

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
            worker = SingleCourseWorker(cookies, cid, u, self.request_interval, self.push_token)
            worker.log_signal.connect(self.log_display.append)
            worker.success_signal.connect(self.highlight_successful_courses)
            worker.finished_signal.connect(self.on_worker_finished)
            worker.captcha_signal.connect(lambda w=worker: self.show_captcha_dialog(w))
            self.workers.append(worker)
            worker.start()
            QThread.msleep(100)

    # === 关键修正: 停止所有类型的线程并复位UI ===
    def stop_selection(self):
        self.is_running = False
        self.log_display.append("⏹️ 正在停止所有线程...")
        
        # 1. 停止普通并发线程
        if self.pre_work_thread and self.pre_work_thread.isRunning():
            self.pre_work_thread.terminate() 
        for w in self.workers:
            if w.isRunning():
                w.stop()
                w.wait() 
        self.workers.clear()
        
        # 2. 停止捡漏线程
        for w in self.pickup_workers:
            if w.isRunning():
                w.stop()
                w.wait()
        self.pickup_workers.clear()

        # 2.5 停止升级线程
        for w in self.upgrade_workers:
            if w.isRunning():
                w.stop()
                w.wait()
        self.upgrade_workers.clear()
        
        # 3. 复位按钮和样式
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

    def show_captcha_dialog(self, worker):
        """显示验证码输入弹窗，用户输入后通知等待中的工作线程"""
        course_label = getattr(worker, 'course_id', None) or getattr(worker, 'course_code', '')
        dialog = CaptchaDialog(self, worker.cookies, caption=course_label)
        if dialog.exec_() == QDialog.Accepted:
            worker.captcha_code = dialog.get_value()
        else:
            worker.captcha_code = "1234"  # 取消则用默认值
        worker.captcha_event.set()
    
    def closeEvent(self, event):
        if self.is_running: self.stop_selection()
        event.accept()

    PICKUP_DATA_FILE = "courses_full.json"

    def _load_pickup_course_map(self):
        """从 courses_full.json 加载 cttId → kcbh 映射及课程名称"""
        if not os.path.exists(self.PICKUP_DATA_FILE):
            return {}, {}
        try:
            with open(self.PICKUP_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            return {}, {}
        ctt_to_kcbh = {}   # cttId → {kcbh, kcmc}
        for course in data.get("courses", []):
            kcbh = course.get("kcbh", "")
            kcmc = course.get("kcmc", "")
            timetable = course.get("timetable")
            if not timetable:
                continue
            for cls in timetable.get("classes", []):
                ctt_id = cls.get("cttId", "")
                if ctt_id:
                    ctt_to_kcbh[ctt_id] = {"kcbh": kcbh, "kcmc": kcmc}
        return ctt_to_kcbh

    def start_pickup_mode_dialog(self):
        u = self.user_combo.currentText()
        if not u:
            QMessageBox.warning(self, "错误", "请先选择一个抢课人")
            return

        all_courses = load_courses().get(u, [])
        if not all_courses:
            QMessageBox.warning(self, "提示", "当前用户没有待抢课程，请先添加课程ID (cttId)。")
            return

        cookies = load_cookies_dict().get(u, "")
        if not cookies:
            QMessageBox.warning(self, "错误", "未找到Cookie，请先更新！")
            return

        # 加载 courses_full.json 查找 cttId 对应的课程信息
        ctt_map = self._load_pickup_course_map()
        if not ctt_map:
            QMessageBox.warning(self, "提示",
                f"未找到 {self.PICKUP_DATA_FILE} 或文件为空。\n"
                "请先运行 fetch_courses.py 生成开课数据文件。")
            return

        # 按课程编号 (kcbh) 分组
        kcbh_groups = {}
        unknown_ctt = []
        for ctt_id in all_courses:
            info = ctt_map.get(ctt_id)
            if info:
                kcbh = info["kcbh"]
                if kcbh not in kcbh_groups:
                    kcbh_groups[kcbh] = {"cttIds": [], "kcmc": info["kcmc"]}
                kcbh_groups[kcbh]["cttIds"].append(ctt_id)
            else:
                unknown_ctt.append(ctt_id)

        if not kcbh_groups and not unknown_ctt:
            QMessageBox.warning(self, "提示",
                f"在 {self.PICKUP_DATA_FILE} 中未找到任何待抢课程对应的开课数据。\n"
                "请确认课程ID (cttId) 正确，或重新运行 fetch_courses.py。")
            return

        # 弹出课程多选窗口（默认全选）
        dialog = SelectCoursesDialog(self, kcbh_groups, unknown_ctt)
        if dialog.exec_() != QDialog.Accepted:
            return

        selected = dialog.get_selected_groups()
        if not selected:
            QMessageBox.information(self, "提示", "未选择任何课程")
            return

        # === 启动捡漏 ===
        self.is_running = True
        self.apply_glassmorphism_style()
        self.log_display.append(f"🚀 正在为 [{u}] 启动智能捡漏模式...")
        self.log_display.append(f"📊 已选择 {len(selected)} 门课程，启动监控线程：")

        for kcbh in sorted(selected.keys()):
            group = selected[kcbh]
            self.log_display.append(f"  🔍 [{kcbh}] {group['kcmc']} ({len(group['cttIds'])} 个班级)")

            worker = PickUpWorker(
                cookies,
                kcbh,
                list(group["cttIds"]),
                u,
                self.request_interval,
                self.push_token,
            )
            worker.log_signal.connect(self.log_display.append)
            worker.success_signal.connect(self.highlight_successful_courses)
            worker.captcha_signal.connect(lambda w=worker: self.show_captcha_dialog(w))
            self.pickup_workers.append(worker)
            worker.start()
            QThread.msleep(500)

        self.start_stop_button.setText(f"⏹️ 停止监控 ({len(selected)} 线程)")
        self.log_display.append(f"✅ 捡漏监控已启动，共 {len(selected)} 个线程")

    def upgrade_course_dialog(self):
        """升级课程：输入当前已选课程 cttId 和目标课程 cttId"""
        u = self.user_combo.currentText()
        if not u:
            QMessageBox.warning(self, "错误", "请先选择一个抢课人")
            return

        # ── 检查数据文件 ──
        if not os.path.exists(self.PICKUP_DATA_FILE):
            QMessageBox.warning(self, "提示",
                f"未找到 {self.PICKUP_DATA_FILE}，请先运行 fetch_courses.py。")
            return

        cookies = load_cookies_dict().get(u, "")
        if not cookies:
            QMessageBox.warning(self, "错误", "未找到 Cookie，请先更新！")
            return

        # ── 输入两个 cttId ──
        current_ctt, ok1 = self._get_text_input("升级课程 — 第一步",
            "请输入当前已选课程的课程编号 (cttId)：\n"
            "（这是你想退掉的已选课程）")
        if not ok1 or not current_ctt:
            return
        current_ctt = current_ctt.strip()

        target_ctt, ok2 = self._get_text_input("升级课程 — 第二步",
            "请输入升级目标的课程编号 (cttId)：\n"
            "（这是你想升级到的目标课程，有空位时自动选入）")
        if not ok2 or not target_ctt:
            return
        target_ctt = target_ctt.strip()

        if current_ctt == target_ctt:
            QMessageBox.warning(self, "错误", "当前课程与目标课程相同，无需升级")
            return

        # ── 查找课程名称供确认 ──
        ctt_map = self._load_pickup_course_map()
        current_info = ctt_map.get(current_ctt)
        target_info = ctt_map.get(target_ctt)

        current_name = f"{current_info['kcmc']} ({current_ctt})" if current_info else current_ctt
        target_name = f"{target_info['kcmc']} ({target_ctt})" if target_info else target_ctt

        if not target_info:
            reply = QMessageBox.question(self, "确认",
                f"未在 {self.PICKUP_DATA_FILE} 中找到目标课程 (cttId={target_ctt})。\n"
                f"仍可能通过课程代码监控，是否继续？",
                QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return

        # ── 确认 ──
        reply = QMessageBox.question(self, "确认升级",
            f"将为 [{u}] 启动升级监控：\n\n"
            f"🔴 当前课程: {current_name}\n"
            f"🟢 目标课程: {target_name}\n\n"
            f"流程：发现目标有空位 → 退掉当前课程 → 选入目标课程\n"
            f"间隔: {self.request_interval}秒\n\n"
            f"是否继续？",
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        # ── 启动升级线程 ──
        self.is_running = True
        self.apply_glassmorphism_style()

        worker = UpgradeWorker(
            cookies, u, current_ctt, target_ctt,
            self.request_interval, self.push_token
        )
        worker.log_signal.connect(self.log_display.append)
        worker.success_signal.connect(lambda msg: self.log_display.append(f"🎉 {msg}"))
        worker.captcha_signal.connect(lambda w=worker: self.show_captcha_dialog(w))
        self.upgrade_workers.append(worker)
        worker.start()

        self.log_display.append(f"\n{'='*45}")
        self.log_display.append(f"🆙 升级监控已启动")
        self.log_display.append(f"  当前: {current_name}")
        self.log_display.append(f"  目标: {target_name}")
        self.log_display.append(f"{'='*45}")

        self.tabs.setCurrentIndex(1)
