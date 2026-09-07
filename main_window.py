# -*- coding: utf-8 -*-
"""
最终修正版：Windows 11 Glassmorphism UI
功能升级：无限轮次 + 多线程并发 + 统一日志 + 定时启动 + 浏览器选择 + 微信推送 + 捡漏模式(完美模拟+交互修正)
"""
import os
import json
import random
import threading
import time
import math
import re
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QComboBox,
    QGridLayout, QFrame, QTabWidget, QMessageBox, QFileDialog,
    QListWidget, QDialog, QSizePolicy, QInputDialog,
    QCheckBox, QScrollArea, QApplication, QFormLayout,
    QDialogButtonBox, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QAbstractItemView
)
from PyQt5.QtGui import QFont, QColor, QCursor, QPixmap
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMutex, QMutexLocker, QTimer, QTime

# 导入课程服务
from course_service import (
    load_accounts, save_accounts, load_courses, save_courses,
    load_cookies_dict, save_cookies_dict, load_delete_courses, save_delete_courses,
    get_cookies, sccourse, cancelSC, send_push_notification,
    query_course_info, access_judge, cleanup_thread_session
)

file_lock = QMutex()
from ui_components import BufferedLogView, InterruptibleThread, workspace_style


class DeletableListWidget(QListWidget):
    """A list whose selected rows can be removed with the Delete key."""

    delete_requested = pyqtSignal()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete and self.selectedIndexes():
            self.delete_requested.emit()
            event.accept()
            return
        super().keyPressEvent(event)

class SingleCourseWorker(InterruptibleThread):
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

    def _wait_for_captcha(self, timeout=120):
        """可中断的验证码等待，每 500ms 检查一次停止标志"""
        start = time.time()
        while time.time() - start < timeout:
            if not self.is_running:
                return False
            if self.captcha_event.wait(timeout=0.5):
                return True
        return False

    def run(self):
        try:
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
                            if self._wait_for_captcha(timeout=120):
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
        finally:
            # 释放线程本地的 HTTP 连接池
            cleanup_thread_session()

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
            from course_service import send_push_notification
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
    def stop(self): super().stop()


# === 捡漏模式工作线程 (修复版) ===
class PickUpWorker(InterruptibleThread):
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

    def _wait_for_captcha(self, timeout=120):
        """可中断的验证码等待，每 500ms 检查一次停止标志"""
        start = time.time()
        while time.time() - start < timeout:
            if not self.is_running:
                return False
            if self.captcha_event.wait(timeout=0.5):
                return True
        return False

    def run(self):
        try:
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
                                                if self._wait_for_captcha(timeout=120):
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
        finally:
            # 释放线程本地的 HTTP 连接池
            cleanup_thread_session()

    def handle_success(self, ctt_id, class_no, course_name):
        msg = f"🎉 捡漏成功！{course_name} (班级:{class_no})"
        self.log_signal.emit(msg)
        self.success_signal.emit(ctt_id)
        
        if self.push_token:
            from course_service import send_push_notification
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
        super().stop()


# === 升级课程线程 ===
class UpgradeWorker(InterruptibleThread):
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

    def __init__(self, cookies, user_name, current_ctt_id, target_ctt_ids, interval=1.0, push_token=""):
        super().__init__()
        self.cookies = cookies
        self.user_name = user_name
        self.current_ctt_id = str(current_ctt_id)
        if isinstance(target_ctt_ids, str):
            target_ctt_ids = [target_ctt_ids]
        self.target_ctt_ids = tuple(dict.fromkeys(
            str(ctt_id).strip() for ctt_id in target_ctt_ids if str(ctt_id).strip()
        ))
        self.interval = interval
        self.push_token = push_token
        self.is_running = True
        self.check_count = 0
        self.use_cap_code = False
        self.captcha_event = threading.Event()
        self.captcha_code = ""
        self._course_data = None  # 缓存 courses_full.json

    def _wait_for_captcha(self, timeout=120):
        """可中断的验证码等待，每 500ms 检查一次停止标志"""
        start = time.time()
        while time.time() - start < timeout:
            if not self.is_running:
                return False
            if self.captcha_event.wait(timeout=0.5):
                return True
        return False

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
        try:
            current_info = self._lookup_kcbh(self.current_ctt_id)
            target_infos = {}
            missing_targets = []
            for target_ctt_id in self.target_ctt_ids:
                target_info = self._lookup_kcbh(target_ctt_id)
                if target_info:
                    target_infos[target_ctt_id] = target_info
                else:
                    missing_targets.append(target_ctt_id)

            if missing_targets:
                self.log_signal.emit(
                    "⚠️ 未在 courses_full.json 中找到备选升级课程："
                    + "、".join(missing_targets)
                )
            if not target_infos:
                self.log_signal.emit("❌ 没有可监控的备选升级课程")
                self.finished_signal.emit()
                return

            current_name = current_info["kcmc"] if current_info else self.current_ctt_id
            targets_by_course = {}
            for target_ctt_id, target_info in target_infos.items():
                targets_by_course.setdefault(target_info["kcbh"], []).append(target_ctt_id)
            target_labels = [
                f"{target_infos[target_ctt_id]['kcmc']} ({target_ctt_id})"
                for target_ctt_id in target_infos
            ]

            self.log_signal.emit(f"🆙 升级线程启动: [{current_name}] → {len(target_infos)} 个备选课程")
            if current_info:
                self.log_signal.emit(f"  当前: {current_info['kcbh']} 班序{current_info['classNo']} "
                                     f"({current_info['enrollCnt']}/{current_info['maxCnt']})")
            for target_label in target_labels:
                self.log_signal.emit(f"  备选: {target_label}")
            self.log_signal.emit("⏳ 等待任一备选课程出现空位...")
            current_course_dropped = False

            while self.is_running:
                found_vacancy = False
                for target_kcbh, target_ctt_ids in targets_by_course.items():
                    if not self.is_running:
                        break
                    try:
                        self.msleep(random.randint(200, 500))
                        res_str = query_course_info(self.cookies, target_kcbh)
                        self.check_count += 1
                        data = json.loads(res_str)
                    except json.JSONDecodeError:
                        if self.check_count % 5 == 0:
                            self.log_signal.emit("⚠️ 查询返回异常，可能被限流")
                        continue
                    except Exception as e:
                        self.log_signal.emit(f"⚠️ 查询备选课程异常: {e}")
                        continue

                    if not data.get("success"):
                        if self.check_count % 5 == 0:
                            self.log_signal.emit(f"⚠️ 查询失败: {data.get('msg', '未知')}")
                        continue

                    for cls in data.get("aaData", []):
                        target_ctt_id = str(cls.get("cttId", ""))
                        if target_ctt_id not in target_ctt_ids:
                            continue
                        enroll = int(cls.get("enrollCnt", 0))
                        max_cnt = int(cls.get("maxCnt", 0))
                        remaining = max_cnt - enroll
                        if remaining <= 0:
                            continue

                        found_vacancy = True
                        target_info = target_infos[target_ctt_id]
                        target_name = target_info["kcmc"]
                        class_no = cls.get("classNo", "?")
                        self.log_signal.emit(f"⚡ 发现空位！[{target_name}] 班级[{class_no}] "
                                             f"余量: {remaining}/{max_cnt}")

                        if current_info and not current_course_dropped:
                            cancel_res = cancelSC(
                                self.cookies, current_info["kcbh"], current_info["classNo"]
                            )
                            self.log_signal.emit(f"📝 退课结果: {cancel_res}")
                            cancel_text = re.sub(r"\s+", "", str(cancel_res))
                            current_course_dropped = (
                                '"success":true' in cancel_text or "成功" in cancel_text
                            )
                            if not current_course_dropped:
                                self.log_signal.emit("⚠️ 退课可能失败，仍尝试选课...")

                        self.log_signal.emit(f"🚀 发起选课请求 -> {target_ctt_id}")
                        cap = "1234" if self.use_cap_code else ""
                        self.use_cap_code = False
                        sc_res = sccourse(self.cookies, target_ctt_id, cap)

                        try:
                            sc_json = json.loads(sc_res)
                            if sc_json.get("msg") == "F":
                                self.log_signal.emit("⚠️ 选课遇到验证码，正在请求用户输入...")
                                self.captcha_code = ""
                                self.captcha_event.clear()
                                self.captcha_signal.emit()
                                if self._wait_for_captcha(timeout=120) and self.captcha_code:
                                    real_cap = self.captcha_code
                                    self.captcha_code = ""
                                    self.log_signal.emit("📝 已获取验证码，重新提交...")
                                    sc_res = sccourse(self.cookies, target_ctt_id, real_cap)
                                else:
                                    self.log_signal.emit("⚠️ 验证码输入超时或为空，继续监控")
                                    continue
                        except (TypeError, ValueError, json.JSONDecodeError):
                            pass

                        if "true" in str(sc_res).lower() or "成功" in str(sc_res):
                            msg = f"🎉 升级成功！{current_name} → {target_name}"
                            self.log_signal.emit(msg)
                            self.success_signal.emit(f"{self.current_ctt_id}→{target_ctt_id}")
                            if self.push_token:
                                send_push_notification(self.push_token, "🆙 升级课程成功", msg)
                            self.is_running = False
                            self.finished_signal.emit()
                            return

                        self.log_signal.emit(f"❌ 选课失败: {sc_res}")
                        self.log_signal.emit("💡 该备选课程可能已被抢走，继续检查其他备选...")

                if not found_vacancy and self.check_count % 10 == 0:
                    self.log_signal.emit(f"👀 ({self.check_count}) 所有备选课程暂无空位，继续监控...")

                # 循环间隔 + 随机抖动
                if self.interval > 0 and self.is_running:
                    jitter = random.uniform(0, self.interval * 0.5)
                    self.msleep(int((self.interval + jitter) * 1000))

            self.log_signal.emit("⏹️ 升级监控已停止")
            self.finished_signal.emit()
        finally:
            # 释放线程本地的 HTTP 连接池
            cleanup_thread_session()

    def stop(self):
        super().stop()

class PreWorkThread(InterruptibleThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    def __init__(self, cookies, delete_list, interval=1):
        super().__init__()
        self.cookies = cookies
        self.delete_list = delete_list
        self.interval = interval
    def run(self):
        try:
            if self.delete_list:
                self.log_signal.emit(f"📌 开始处理待删除课程 ({len(self.delete_list)}门)")
            for item in self.delete_list:
                if not self.is_running:
                    break
                cc, cn = item.get("courseCode", ""), item.get("classNo", "")
                self.log_signal.emit(f"⏳ 正在删除: {cc} (班序: {cn})")
                try:
                    self.log_signal.emit(f"  📝 结果: {cancelSC(self.cookies, cc, cn)}")
                except Exception as e:
                    self.log_signal.emit(f"  ⚠️ 异常: {e}")
                self.msleep(int(self.interval * 1000))
            if self.is_running:
                self.finished_signal.emit()
        finally:
            cleanup_thread_session()


class CookieUpdateWorker(InterruptibleThread):
    log_signal = pyqtSignal(str)
    result_signal = pyqtSignal(int, int)

    def __init__(self, accounts, parent=None):
        super().__init__(parent)
        self.accounts = accounts

    def run(self):
        success = failures = 0
        try:
            for index, account in enumerate(self.accounts, 1):
                if not self.is_running:
                    break
                name = account['name']
                self.log_signal.emit(f"[{index}/{len(self.accounts)}] 正在更新 {name}")
                try:
                    cookies = get_cookies(account['username'], account['password'],
                                          report_callback=self.log_signal.emit)
                    if not cookies:
                        raise RuntimeError("未获取到有效 Cookie")
                    with QMutexLocker(file_lock):
                        saved = load_cookies_dict()
                        saved[name] = '; '.join(f"{c['name']}={c['value']}" for c in cookies)
                        save_cookies_dict(saved)
                    success += 1
                    self.log_signal.emit(f"✓ {name} 更新成功")
                except Exception as exc:
                    failures += 1
                    self.log_signal.emit(f"更新失败 [{name}]: {exc}")
            self.result_signal.emit(success, failures)
        finally:
            cleanup_thread_session()

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
        self.setStyleSheet(workspace_style(self.dark_mode))
    def get_value(self):
        return self.input_field.toPlainText() if isinstance(self.input_field, QTextEdit) else self.input_field.text()


class CaptchaImageWorker(QThread):
    image_signal = pyqtSignal(bytes)
    error_signal = pyqtSignal(str)

    def __init__(self, cookies, parent=None):
        super().__init__(parent)
        self.cookies = cookies

    def run(self):
        try:
            import requests
            with requests.get(
                "https://jwgl.dhu.edu.cn/dhu/captcha/code",
                headers={
                    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                                   "Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"),
                    "Referer": "https://jwgl.dhu.edu.cn/dhu/selectcourse/toSH",
                },
                cookies=self.cookies, timeout=15,
            ) as response:
                response.raise_for_status()
                self.image_signal.emit(response.content)
        except Exception as exc:
            self.error_signal.emit(f"加载失败，点击刷新重试: {exc}")


class CaptchaDialog(QDialog):
    """验证码输入弹窗 - 从服务器获取验证码图片并让用户输入"""
    def __init__(self, parent, cookies, caption=""):
        super().__init__(parent)
        self.setWindowTitle("验证码输入")
        self.setMinimumSize(420, 320)
        self.cookies = cookies
        self.dark_mode = getattr(parent, 'dark_mode', False)
        self._cap_code = ""
        self.image_worker = None
        self._pending_result = None
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
        self.refresh_button = refresh_btn
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
        if self.image_worker is not None:
            return
        self.image_label.setText("⏳ 加载验证码中...")
        self.refresh_button.setEnabled(False)
        self.image_worker = CaptchaImageWorker(self._parse_cookies(), self)
        self.image_worker.image_signal.connect(self._show_captcha_image)
        self.image_worker.error_signal.connect(self.image_label.setText)
        self.image_worker.finished.connect(self._image_finished)
        self.image_worker.start()

    def _show_captcha_image(self, content):
        pixmap = QPixmap()
        if pixmap.loadFromData(content):
            self.image_label.setPixmap(pixmap.scaledToHeight(80, Qt.SmoothTransformation))
        else:
            self.image_label.setText("图片解析失败，点击刷新重试")

    def _image_finished(self):
        self.image_worker.deleteLater()
        self.image_worker = None
        self.refresh_button.setEnabled(True)
        if self._pending_result is not None:
            self.done(self._pending_result)

    def done(self, result):
        if self.image_worker is not None:
            self._pending_result = result
            self.image_label.setText("正在结束图片请求…")
            return
        super().done(result)

    def get_value(self):
        return self.input_field.text().strip()

    def _apply_style(self):
        self.setStyleSheet(workspace_style(self.dark_mode))


# === 多选账号弹窗 ===
class SelectAccountsDialog(QDialog):
    """Responsive account picker used by the Cookie refresh workflow."""

    def __init__(self, parent, accounts):
        super().__init__(parent)
        self.setWindowTitle("更新 Cookie")
        self.setMinimumSize(520, 380)
        self.resize(
            max(520, min(760, int(parent.width() * 0.68))),
            max(380, min(620, int(parent.height() * 0.72))),
        )
        self.dark_mode = getattr(parent, 'dark_mode', False)
        self.setObjectName("SelectAccountsDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        title = QLabel("更新账号 Cookie")
        title.setObjectName("Title")
        layout.addWidget(title)
        description = QLabel("选择需要重新登录的账号。更新在后台依次执行，期间界面仍可正常操作。")
        description.setObjectName("Muted")
        description.setWordWrap(True)
        layout.addWidget(description)

        controls = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索姓名或学号")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._filter_accounts)
        controls.addWidget(self.search_input, 1)
        self.select_all_cb = QCheckBox("选择全部")
        self.select_all_cb.stateChanged.connect(self._on_select_all)
        controls.addWidget(self.select_all_cb)
        layout.addLayout(controls)

        self.account_tree = QTreeWidget()
        self.account_tree.setColumnCount(3)
        self.account_tree.setHeaderLabels(("选课人", "学号", "Cookie 状态"))
        self.account_tree.setRootIsDecorated(False)
        self.account_tree.setAlternatingRowColors(True)
        self.account_tree.setUniformRowHeights(True)
        self.account_tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.account_tree.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.account_tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.account_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.account_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.account_tree.itemChanged.connect(self._update_count)
        self.account_tree.itemSelectionChanged.connect(self._update_count)

        self.account_items = []
        cookies_dict = load_cookies_dict()
        for acc in accounts:
            name = acc["name"]
            uid = acc["username"]
            status = "已有 Cookie" if cookies_dict.get(name) else "需要更新"
            item = QTreeWidgetItem((name, uid, status))
            item.setCheckState(0, Qt.Unchecked)
            item.acc_info = acc
            self.account_tree.addTopLevelItem(item)
            self.account_items.append(item)
        layout.addWidget(self.account_tree, 1)

        info_layout = QHBoxLayout()
        self.count_label = QLabel(f"已选择 0 / {len(accounts)} 个账号")
        self.count_label.setObjectName("Muted")
        info_layout.addWidget(self.count_label)
        info_layout.addStretch()

        ok_btn = QPushButton("确定更新")
        ok_btn.setObjectName("Primary")
        ok_btn.setMinimumSize(120, 38)
        ok_btn.clicked.connect(self.accept)
        info_layout.addWidget(ok_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumSize(80, 38)
        cancel_btn.clicked.connect(self.reject)
        info_layout.addWidget(cancel_btn)

        layout.addLayout(info_layout)
        self._update_count()
        self._apply_style()

    def _on_select_all(self, state):
        checked = state == Qt.Checked
        self.account_tree.blockSignals(True)
        for item in self.account_items:
            if not item.isHidden():
                item.setCheckState(0, Qt.Checked if checked else Qt.Unchecked)
        self.account_tree.blockSignals(False)
        self._update_count()

    def _filter_accounts(self, text):
        query = text.strip().casefold()
        for item in self.account_items:
            hidden = query not in f"{item.text(0)} {item.text(1)}".casefold()
            item.setHidden(hidden)
            if hidden:
                item.setSelected(False)
        self._update_count()

    def _update_count(self):
        selected = sum(item.checkState(0) == Qt.Checked or item.isSelected()
                       for item in self.account_items)
        total = len(self.account_items)
        self.count_label.setText(f"已选择 {selected} / {total} 个账号")

    def get_selected_accounts(self):
        return [item.acc_info for item in self.account_items
                if item.checkState(0) == Qt.Checked or item.isSelected()]

    def _apply_style(self):
        self.setStyleSheet(workspace_style(self.dark_mode))


class AccountEditorDialog(QDialog):
    """Add or edit one account without exposing its password."""

    def __init__(self, parent, account=None):
        super().__init__(parent)
        self.dark_mode = getattr(parent, "dark_mode", False)
        self.setWindowTitle("编辑选课人" if account else "添加选课人")
        self.setMinimumWidth(440)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(16)
        title = QLabel(self.windowTitle())
        title.setObjectName("Title")
        layout.addWidget(title)
        form = QFormLayout()
        form.setSpacing(12)
        self.name_input = QLineEdit((account or {}).get("name", ""))
        self.name_input.setPlaceholderText("用于界面显示")
        self.username_input = QLineEdit((account or {}).get("username", ""))
        self.username_input.setPlaceholderText("学号")
        self.password_input = QLineEdit((account or {}).get("password", ""))
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("统一身份认证密码")
        form.addRow("显示名称", self.name_input)
        form.addRow("学号", self.username_input)
        form.addRow("密码", self.password_input)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Cancel | QDialogButtonBox.Save)
        buttons.button(QDialogButtonBox.Save).setText("保存")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setStyleSheet(workspace_style(self.dark_mode))

    def accept(self):
        if not all((self.name_input.text().strip(), self.username_input.text().strip(),
                    self.password_input.text())):
            QMessageBox.warning(self, "信息不完整", "名称、学号和密码都不能为空。")
            return
        super().accept()

    def account(self):
        return {
            "name": self.name_input.text().strip(),
            "username": self.username_input.text().strip(),
            "password": self.password_input.text(),
        }


class ManageAccountsDialog(QDialog):
    """Manage account records and their associated local configuration."""

    def __init__(self, parent, accounts):
        super().__init__(parent)
        self.dark_mode = getattr(parent, "dark_mode", False)
        self.accounts = [dict(account) for account in accounts]
        self.changed = False
        self.setWindowTitle("管理选课人")
        self.setMinimumSize(560, 420)
        self.resize(max(560, min(760, int(parent.width() * 0.65))),
                    max(420, min(620, int(parent.height() * 0.7))))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)
        title = QLabel("管理选课人")
        title.setObjectName("Title")
        layout.addWidget(title)
        description = QLabel("账号名称用于关联课程计划、Cookie 和待退课程。")
        description.setObjectName("Muted")
        layout.addWidget(description)
        self.account_list = QListWidget()
        self.account_list.setUniformItemSizes(True)
        self.account_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.account_list.itemDoubleClicked.connect(lambda _item: self._edit_account())
        layout.addWidget(self.account_list, 1)
        actions = QHBoxLayout()
        add_button = QPushButton("+ 添加")
        add_button.setObjectName("Primary")
        add_button.clicked.connect(self._add_account)
        actions.addWidget(add_button)
        edit_button = QPushButton("编辑")
        edit_button.clicked.connect(self._edit_account)
        actions.addWidget(edit_button)
        delete_button = QPushButton("删除")
        delete_button.clicked.connect(self._delete_account)
        actions.addWidget(delete_button)
        actions.addStretch()
        close_button = QPushButton("完成")
        close_button.clicked.connect(self.accept)
        actions.addWidget(close_button)
        layout.addLayout(actions)
        self._refresh()
        self.setStyleSheet(workspace_style(self.dark_mode))

    def _refresh(self, selected_row=None):
        self.account_list.clear()
        for account in self.accounts:
            self.account_list.addItem(f"{account['name']}    ·    {account['username']}")
        if self.accounts:
            row = min(selected_row if selected_row is not None else 0, len(self.accounts) - 1)
            self.account_list.setCurrentRow(max(0, row))

    def _selected_row(self):
        rows = sorted({index.row() for index in self.account_list.selectedIndexes()})
        if not rows:
            QMessageBox.information(self, "请选择选课人", "请先在列表中选择一个选课人。")
            return None
        if len(rows) > 1:
            QMessageBox.information(self, "请选择一个选课人", "编辑时只能选择一个选课人。")
            return None
        return rows[0]

    def _name_is_available(self, name, ignore_row=None):
        return all(index == ignore_row or account["name"] != name
                   for index, account in enumerate(self.accounts))

    def _add_account(self):
        dialog = AccountEditorDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        account = dialog.account()
        if not self._name_is_available(account["name"]):
            QMessageBox.warning(self, "名称重复", "选课人名称必须唯一。")
            return
        self.accounts.append(account)
        save_accounts(self.accounts)
        self.changed = True
        self._refresh(len(self.accounts) - 1)

    def _edit_account(self):
        row = self._selected_row()
        if row is None:
            return
        previous = self.accounts[row]
        dialog = AccountEditorDialog(self, previous)
        if dialog.exec_() != QDialog.Accepted:
            return
        account = dialog.account()
        if not self._name_is_available(account["name"], ignore_row=row):
            QMessageBox.warning(self, "名称重复", "选课人名称必须唯一。")
            return
        self.accounts[row] = account
        save_accounts(self.accounts)
        if previous["name"] != account["name"]:
            self._rename_linked_data(previous["name"], account["name"])
        self.changed = True
        self._refresh(row)

    def _rename_linked_data(self, old_name, new_name):
        for loader, saver in ((load_courses, save_courses),
                              (load_delete_courses, save_delete_courses),
                              (load_cookies_dict, save_cookies_dict)):
            data = loader()
            if old_name in data:
                data[new_name] = data.pop(old_name)
                saver(data)

    def _delete_account(self):
        rows = sorted({index.row() for index in self.account_list.selectedIndexes()}, reverse=True)
        if not rows:
            QMessageBox.information(self, "请选择选课人", "请先在列表中选择要删除的选课人。")
            return
        selected_accounts = [self.accounts[row] for row in reversed(rows)]
        account_names = [account["name"] for account in selected_accounts]
        target = f"“{account_names[0]}”" if len(account_names) == 1 else f"选中的 {len(account_names)} 个选课人"
        answer = QMessageBox.question(
            self,
            "删除选课人",
            f"确定删除{target}吗？\n关联的课程计划和 Cookie 也会一并删除。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        for row in rows:
            self.accounts.pop(row)
        save_accounts(self.accounts)
        for loader, saver in ((load_courses, save_courses),
                              (load_delete_courses, save_delete_courses),
                              (load_cookies_dict, save_cookies_dict)):
            data = loader()
            changed = False
            for name in account_names:
                if name in data:
                    del data[name]
                    changed = True
            if changed:
                saver(data)
        self.changed = True
        self._refresh(min(rows))


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
        self.setStyleSheet(workspace_style(self.dark_mode))

class ProductionGlassmorphismUI(QMainWindow):
    """主界面类"""
    def __init__(self):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("CourseSelect · 选课工作台")
        self.setGeometry(50, 50, 1200, 800)
        self.setMinimumSize(960, 700)
        
        self.workers = []
        self.pickup_workers = []
        self.upgrade_workers = []
        self.pre_work_thread = None
        self.is_running = False
        self._managed_workers = set()
        self._pending_workers = set()
        self._stopping = False
        self._closing = False
        self.cookie_worker = None
        self.query_panel = None
        self._close_timer = QTimer(self)
        self._close_timer.setInterval(100)
        self._close_timer.timeout.connect(self.close)
        self.request_interval = 1.0
        self.dark_mode = True

        self.scheduled_time = None
        self.scheduled_triggered = False
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
                    self.dark_mode = data.get("dark_mode", True)
        except: pass
    def save_settings(self):
        try:
            data = {}
            if os.path.exists("settings.json"):
                with open("settings.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
            data["push_token"] = self.push_token
            data["dark_mode"] = self.dark_mode
            with open("settings.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except: pass

    def create_menu_bar(self):
        menubar = self.menuBar()
        menubar.setFont(QFont("Microsoft YaHei UI", 12))
        
        file_menu = menubar.addMenu("文件")
        file_menu.addAction("导入配置目录").triggered.connect(self.import_config_directory)
        file_menu.addSeparator()
        file_menu.addAction("退出").triggered.connect(self.close)

        settings_menu = menubar.addMenu("设置")
        self.manage_accounts_action = settings_menu.addAction("管理选课人")
        self.manage_accounts_action.triggered.connect(self.manage_accounts_dialog)
        settings_menu.addSeparator()
        settings_menu.addAction("并发/查询间隔").triggered.connect(self.set_request_interval)
        settings_menu.addAction("配置微信推送").triggered.connect(self.set_push_token_dialog)
        settings_menu.addSeparator()
        self.theme_action = settings_menu.addAction("切换为浅色模式" if self.dark_mode else "切换为深色模式")
        self.theme_action.triggered.connect(self.toggle_theme)
    
    def create_central_ui(self):
        self.central_widget = QWidget()
        self.central_widget.setObjectName("CentralWidget")
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(28, 20, 28, 20)
        main_layout.setSpacing(14)
        heading = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(2)
        eyebrow = QLabel("COURSESELECT  /  WORKSPACE")
        eyebrow.setObjectName("Eyebrow")
        eyebrow.setFixedHeight(18)
        titles.addWidget(eyebrow)
        self.title_label = QLabel("选课工作台")
        self.title_label.setObjectName("Title")
        self.title_label.setFixedHeight(40)
        titles.addWidget(self.title_label)
        subtitle = QLabel("管理课程计划，随时掌握选课进度。")
        subtitle.setObjectName("Muted")
        subtitle.setFixedHeight(20)
        titles.addWidget(subtitle)
        heading.addLayout(titles)
        heading.addStretch()
        theme_button = QPushButton("切换外观")
        theme_button.clicked.connect(self.toggle_theme)
        heading.addWidget(theme_button)
        self.status_label = QLabel("准备就绪")
        self.status_label.setObjectName("Status")
        self.status_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.status_label.setAlignment(Qt.AlignCenter)
        heading.addWidget(self.status_label)
        main_layout.addLayout(heading)
        main_layout.addWidget(self._create_user_section())

        metrics = QHBoxLayout()
        self.metric_labels = []
        self.metric_cards = []
        for title, value, hint in (("待选课程", "0", "本次计划选入的课程"),
                                   ("待退课程", "0", "启动后会先执行退课"),
                                   ("请求间隔", "1.0 s", "可在设置中调整")):
            card = QFrame()
            card.setObjectName("Card")
            box = QVBoxLayout(card)
            box.setContentsMargins(18, 10, 18, 10)
            box.setSpacing(3)
            label = QLabel(title)
            label.setObjectName("Muted")
            box.addWidget(label)
            number = QLabel(value)
            number.setObjectName("Metric")
            box.addWidget(number)
            note = QLabel(hint)
            note.setObjectName("Muted")
            box.addWidget(note)
            self.metric_labels.append(number)
            self.metric_cards.append(card)
            metrics.addWidget(card)
        main_layout.addLayout(metrics)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_courses_tab(), "课程计划")
        self.tabs.addTab(self._create_logs_tab(), "运行日志")
        from course_query_window import CourseQueryUI
        self.query_panel = CourseQueryUI(
            self,
            embedded=True,
            cookie_provider=self._current_query_cookie,
            course_add_callback=self.add_course_from_query,
        )
        self.query_tab_index = self.tabs.addTab(self.query_panel, "开课查询")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tabs, 1)
        footer = QHBoxLayout()
        self.footer_hint = QLabel("核对课程计划后开始 · 定时启动与推送可在设置中配置")
        self.footer_hint.setObjectName("Muted")
        footer.addWidget(self.footer_hint, 1)
        self.start_stop_button = QPushButton("开始选课")
        self.start_stop_button.setObjectName("Primary")
        self.start_stop_button.setMinimumSize(220, 48)
        self.start_stop_button.clicked.connect(self.toggle_selection)
        footer.addWidget(self.start_stop_button)
        main_layout.addLayout(footer)
        for button in self.central_widget.findChildren(QPushButton):
            button.setCursor(QCursor(Qt.PointingHandCursor))

    def _create_user_section(self):
        frame = QFrame()
        frame.setObjectName("Card")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)
        layout.addWidget(QLabel("当前账号"))
        self.user_combo = QComboBox()
        self.user_combo.setMinimumWidth(180)
        self.user_combo.setMinimumHeight(38)
        self.user_combo.currentTextChanged.connect(self.on_user_changed)
        layout.addWidget(self.user_combo, 1)
        self.add_account_button = QPushButton("+")
        self.add_account_button.setToolTip("添加选课人")
        self.add_account_button.setAccessibleName("添加选课人")
        self.add_account_button.setFixedSize(38, 38)
        self.add_account_button.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.add_account_button.clicked.connect(self.new_account_dialog)
        layout.addWidget(self.add_account_button)
        self.user_info_label = QLabel("选择账号以查看课程计划")
        self.user_info_label.setObjectName("Muted")
        layout.addWidget(self.user_info_label, 1)
        self.cookie_button = QPushButton("更新 Cookie")
        self.cookie_button.clicked.connect(self.update_cookie_dialog)
        layout.addWidget(self.cookie_button)
        query_button = QPushButton("查询开课数据")
        query_button.clicked.connect(self.open_course_query)
        layout.addWidget(query_button)
        return frame

    def _create_courses_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 12, 0, 0)
        columns = QHBoxLayout()
        for title, hint, attr, callback in (
            ("待选课程", "添加课程编号；选择后按 Delete 删除", "course_list", self.add_new_course),
            ("待退课程", "启动前优先退选；选择后按 Delete 删除", "delete_course_list", self.add_delete_course),
        ):
            card = QFrame()
            card.setObjectName("Card")
            box = QVBoxLayout(card)
            box.setContentsMargins(16, 14, 16, 14)
            row = QHBoxLayout()
            row.addWidget(QLabel(title), 1)
            add = QPushButton("+ 添加课程")
            add.setMinimumHeight(36)
            add.clicked.connect(callback)
            row.addWidget(add)
            box.addLayout(row)
            note = QLabel(hint)
            note.setObjectName("Muted")
            box.addWidget(note)
            view = DeletableListWidget()
            view.setMinimumHeight(70)
            view.setUniformItemSizes(True)
            view.setSelectionMode(QAbstractItemView.ExtendedSelection)
            view.setToolTip("选择课程后按 Delete 删除")
            setattr(self, attr, view)
            if attr == "course_list":
                view.delete_requested.connect(self.delete_selected_courses)
            else:
                view.delete_requested.connect(self.delete_selected_drop_courses)
            box.addWidget(view, 1)
            empty = QLabel("暂无课程 · 点击上方添加")
            empty.setObjectName("Muted")
            empty.setAlignment(Qt.AlignCenter)
            setattr(self, attr + "_empty", empty)
            box.addWidget(empty)
            columns.addWidget(card)
        layout.addLayout(columns, 1)
        actions = QHBoxLayout()
        self.task_buttons = []
        for text, callback in (("捡漏监控", self.start_pickup_mode_dialog),
                               ("升级课程", self.upgrade_course_dialog),
                               ("定时启动", self.set_schedule_dialog)):
            button = QPushButton(text)
            button.clicked.connect(callback)
            actions.addWidget(button)
            self.task_buttons.append(button)
        actions.addStretch()
        layout.addLayout(actions)
        return widget

    def _create_logs_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 12, 0, 0)
        row = QHBoxLayout()
        note = QLabel("保留最近 3,000 行 · 向上滚动可暂停自动跟随")
        note.setObjectName("Muted")
        row.addWidget(note, 1)
        clear = QPushButton("清空日志")
        row.addWidget(clear)
        layout.addLayout(row)
        self.log_display = BufferedLogView()
        self.log_display.setFont(QFont("Consolas", 10))
        clear.clicked.connect(self.log_display.clear)
        layout.addWidget(self.log_display)
        return widget

    def open_course_query(self):
        self.tabs.setCurrentIndex(self.query_tab_index)

    def _current_query_cookie(self):
        user = self.user_combo.currentText()
        if not user:
            return "", ""
        return user, load_cookies_dict().get(user, "")

    def add_course_from_query(self, course_id):
        user = self.user_combo.currentText()
        if not user:
            QMessageBox.warning(self, "未选择账号", "请先在工作台选择一个账号。")
            return False
        courses = load_courses()
        user_courses = courses.setdefault(user, [])
        if course_id in user_courses:
            QMessageBox.information(self, "课程已存在", "这门课程已经在待选计划中。")
            return False
        user_courses.append(course_id)
        save_courses(courses)
        self.on_user_changed(user)
        self.log_display.append(f"已从开课查询加入待选课程：{course_id}")
        return True

    def _on_tab_changed(self, index):
        show_selection = index != self.query_tab_index
        for card in self.metric_cards:
            card.setVisible(show_selection)
        self.footer_hint.setVisible(show_selection)
        self.start_stop_button.setVisible(show_selection)

    def apply_glassmorphism_style(self):
        self.setStyleSheet(workspace_style(self.dark_mode))
        if self.query_panel is not None:
            self.query_panel.set_dark_mode(self.dark_mode)
        self._update_run_state()

    def _update_run_state(self):
        stopping = self._stopping or self._closing
        self.start_stop_button.setProperty("running", self.is_running)
        self.start_stop_button.setText("正在停止…" if stopping else
                                       "停止所有任务" if self.is_running else "开始选课")
        self.start_stop_button.setEnabled(not stopping and bool(self.user_combo.currentText()))
        self.user_combo.setEnabled(not self.is_running and not stopping)
        account_editable = not self.is_running and not stopping and self.cookie_worker is None
        self.add_account_button.setEnabled(account_editable)
        self.manage_accounts_action.setEnabled(account_editable)
        self.cookie_button.setEnabled(account_editable)
        self.course_list.setEnabled(not self.is_running and not stopping)
        self.delete_course_list.setEnabled(not self.is_running and not stopping)
        for button in self.task_buttons:
            button.setEnabled(not self.is_running and not stopping)
        self.status_label.setText("正在停止" if stopping else "任务运行中" if self.is_running else "准备就绪")
        self.start_stop_button.style().unpolish(self.start_stop_button)
        self.start_stop_button.style().polish(self.start_stop_button)

    def load_initial_data(self):
        try:
            current_user = self.user_combo.currentText()
            accounts = load_accounts()
            self.user_combo.blockSignals(True)
            self.user_combo.clear()
            self.user_combo.addItem("")
            for acc in accounts:
                self.user_combo.addItem(acc["name"])
            if current_user:
                index = self.user_combo.findText(current_user)
                if index >= 0:
                    self.user_combo.setCurrentIndex(index)
            self.user_combo.blockSignals(False)
            self.log_display.append("✓ 系统就绪")
            self.on_user_changed(self.user_combo.currentText())
        except: pass

    def on_user_changed(self, username):
        self.course_list.clear()
        self.delete_course_list.clear()
        self.user_info_label.setText("选择账号以查看课程计划")
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
        except Exception as exc:
            self.log_display.append(f"读取课程计划失败: {exc}")
        self.metric_labels[0].setText(str(self.course_list.count()))
        self.metric_labels[1].setText(str(self.delete_course_list.count()))
        self.course_list_empty.setVisible(self.course_list.count() == 0)
        self.delete_course_list_empty.setVisible(self.delete_course_list.count() == 0)
        self._update_run_state()

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
        if self.is_running or self.cookie_worker is not None:
            return
        dialog = AccountEditorDialog(self)
        if dialog.exec_() != QDialog.Accepted:
            return
        account = dialog.account()
        accounts = load_accounts()
        if any(item["name"] == account["name"] for item in accounts):
            QMessageBox.warning(self, "名称重复", "选课人名称必须唯一。")
            return
        accounts.append(account)
        save_accounts(accounts)
        self.load_initial_data()
        self.user_combo.setCurrentText(account["name"])

    def manage_accounts_dialog(self):
        if self.is_running or self.cookie_worker is not None:
            return
        dialog = ManageAccountsDialog(self, load_accounts())
        dialog.exec_()
        if dialog.changed:
            self.load_initial_data()

    def delete_selected_courses(self):
        self._delete_selected_plan_rows(self.course_list, is_drop=False)

    def delete_selected_drop_courses(self):
        self._delete_selected_plan_rows(self.delete_course_list, is_drop=True)

    def _delete_selected_plan_rows(self, widget, is_drop):
        if self.is_running or self._stopping:
            return
        user = self.user_combo.currentText()
        rows = sorted({index.row() for index in widget.selectedIndexes()}, reverse=True)
        if not user or not rows:
            return
        kind = "待退课程" if is_drop else "待选课程"
        answer = QMessageBox.question(
            self,
            f"删除{kind}",
            f"确定从计划中删除选中的 {len(rows)} 门课程吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        loader = load_delete_courses if is_drop else load_courses
        saver = save_delete_courses if is_drop else save_courses
        data = loader()
        planned = data.get(user, [])
        removed = 0
        for row in rows:
            if 0 <= row < len(planned):
                planned.pop(row)
                removed += 1
        data[user] = planned
        saver(data)
        self.on_user_changed(user)
        self.log_display.append(f"已从{kind}中删除 {removed} 项")
    
    def check_schedule(self):
        if self.scheduled_time and not self.is_running and not self.scheduled_triggered:
            target = QTime.fromString(self.scheduled_time, "HH:mm:ss")
            if not target.isValid():
                return
            current = QTime.currentTime()
            # ±1 秒容差窗口，避免主线程阻塞错过精确时间点
            diff_seconds = abs(current.secsTo(target))
            if diff_seconds <= 1:
                self.scheduled_triggered = True
                current_str = current.toString("HH:mm:ss")
                self.log_display.append(f"⏰ 触发定时任务: {current_str} (目标: {self.scheduled_time})")
                self.toggle_selection()
                self.scheduled_time = None
                self.title_label.setText(f"⚡ 智能抢课系统 Pro (并发版)")

    def set_schedule_dialog(self):
        time_str, ok = self._get_text_input("定时启动", "输入启动时间 (HH:mm:ss):")
        if ok and time_str:
            time_str = time_str.strip()
            # 解析并规范化时间格式，同时验证有效性
            parts = time_str.split(':')
            if len(parts) == 3:
                try:
                    h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                    normalized = QTime(h, m, s)
                    if normalized.isValid():
                        self.scheduled_time = normalized.toString("HH:mm:ss")
                        self.scheduled_triggered = False
                        self.log_display.append(f"⏰ 定时已设置: {self.scheduled_time}")
                        self.title_label.setText(f"⚡ 智能抢课系统 Pro (定时: {self.scheduled_time})")
                    else:
                        QMessageBox.warning(self, "格式错误", "时间无效，请使用正确的 HH:mm:ss 格式，例如 12:59:59")
                except ValueError:
                    QMessageBox.warning(self, "格式错误", "请使用正确的 HH:mm:ss 格式，例如 12:59:59")
            else:
                QMessageBox.warning(self, "格式错误", "请使用 HH:mm:ss 格式，例如 12:59:59")

    def set_push_token_dialog(self):
        token, ok = self._get_text_input("微信推送配置", "请输入 PushPlus Token (留空则关闭):")
        if ok:
            self.push_token = token.strip()
            self.save_settings()
            if self.push_token:
                self.log_display.append(f"📲 推送 Token 已保存: {self.push_token[:4]}****")
                from course_service import send_push_notification
                send_push_notification(self.push_token, "抢课系统测试", "您的 Token 配置成功！")
            else:
                self.log_display.append("📲 推送功能已关闭")

    def update_cookie_dialog(self):
        """弹出账号多选窗口，为选中的账号依次获取 Cookie"""
        if self.cookie_worker is not None or self._closing:
            return
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

        self.cookie_worker = CookieUpdateWorker(selected, self)
        self._update_run_state()
        self.tabs.setCurrentIndex(1)
        self.log_display.append(f"开始更新 {len(selected)} 个账号的 Cookie…")
        self.cookie_worker.log_signal.connect(self.log_display.append)
        self.cookie_worker.result_signal.connect(
            lambda ok, failed: self.log_display.append(f"Cookie 更新完成：成功 {ok}，失败 {failed}"))
        self.cookie_worker.finished.connect(self._cookie_update_finished)
        self.cookie_worker.start()

    def _cookie_update_finished(self):
        self.cookie_worker.deleteLater()
        self.cookie_worker = None
        self._update_run_state()
        self.on_user_changed(self.user_combo.currentText())
        if self._closing:
            QTimer.singleShot(0, self.close)

    def set_request_interval(self):
        s, ok = self._get_text_input("设置", "并发间隔(秒):")
        if ok:
            try:
                val = float(s)
                if not math.isfinite(val) or val <= 0:
                    raise ValueError("间隔必须是大于 0 的有限数值")
                self.request_interval = val
                self.metric_labels[2].setText(f"{val:g} s")
            except ValueError:
                QMessageBox.warning(self, "输入无效", "请输入大于 0 的有效秒数。")

    # === 关键修正: 统一的启动/停止逻辑 ===
    def toggle_selection(self):
        if self._stopping or self._closing:
            return
        # 如果正在运行（无论是普通抢课还是捡漏监控），都调用停止
        if self.is_running or self.pickup_workers:
            self.stop_selection()
        else:
            self.start_selection()

    def start_selection(self):
        if self.is_running or self._stopping or self._closing:
            return
        u = self.user_combo.currentText()
        if not u: return
        self.is_running = True
        self._update_run_state()
        self.tabs.setCurrentIndex(1)
        
        d_courses = load_delete_courses().get(u, [])
        cookies = load_cookies_dict().get(u, "")
        if not cookies:
            self.log_display.append("❌ 未找到Cookie，请先更新！")
            self.stop_selection()
            return

        self.pre_work_thread = PreWorkThread(cookies, d_courses)
        self.pre_work_thread.log_signal.connect(self.log_display.append)
        self.pre_work_thread.finished.connect(lambda: self.launch_concurrent_workers(u, cookies))
        self._queue_worker(self.pre_work_thread)

    def launch_concurrent_workers(self, u, cookies):
        if not self.is_running: return
        courses = load_courses().get(u, [])
        if not courses:
            self.log_display.append("⚠️ 没有待选课程")
            self.stop_selection()
            return
        self.log_display.append(f"🚀 启动并发引擎: {len(courses)} 个线程并行处理...")
        self.workers = []
        for index, cid in enumerate(courses):
            worker = SingleCourseWorker(cookies, cid, u, self.request_interval, self.push_token)
            worker.log_signal.connect(self.log_display.append)
            worker.success_signal.connect(self.highlight_successful_courses)
            worker.finished_signal.connect(self.on_worker_finished)
            worker.captcha_signal.connect(lambda w=worker: self.show_captcha_dialog(w))
            self.workers.append(worker)
            self._queue_worker(worker, index * 100)

    def _queue_worker(self, worker, delay=0):
        # Keep running and scheduled threads alive until they actually finish.
        worker.setParent(self)
        self._managed_workers.add(worker)
        self._pending_workers.add(worker)
        worker.finished.connect(lambda w=worker: self._release_worker(w))
        QTimer.singleShot(delay, lambda w=worker: self._start_queued_worker(w))

    def _start_queued_worker(self, worker):
        if worker not in self._pending_workers:
            return
        self._pending_workers.remove(worker)
        if self.is_running and not self._closing:
            worker.start()
        else:
            self._release_worker(worker)

    def _release_worker(self, worker):
        self._managed_workers.discard(worker)
        self._pending_workers.discard(worker)
        for group in (self.workers, self.pickup_workers, self.upgrade_workers):
            if worker in group:
                group.remove(worker)
        if self.pre_work_thread is worker:
            self.pre_work_thread = None
        worker.deleteLater()
        QTimer.singleShot(0, self._finish_selection_if_idle)

    def _finish_selection_if_idle(self):
        if self._managed_workers:
            return
        was_active = self.is_running or self._stopping
        self.is_running = False
        self._stopping = False
        self._update_run_state()
        if was_active:
            self.log_display.append("✓ 所有任务已结束")
        if self._closing:
            self.close()

    def stop_selection(self):
        self.is_running = False
        self._stopping = bool(self._managed_workers)
        self.log_display.append("正在停止任务，等待当前请求结束…")
        for worker in tuple(self._managed_workers):
            worker.stop()
            if worker in self._pending_workers:
                self._release_worker(worker)
        self._update_run_state()
        self._finish_selection_if_idle()

    def on_worker_finished(self, course_id):
        # QThread.finished handles lifecycle after run() and cleanup return.
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
        self.save_settings()
        if self.query_panel is not None:
            self.query_panel.set_dark_mode(self.dark_mode)
        self.log_display.append("✓ 主题已切换")

    def _get_text_input(self, title, prompt, is_multiline=False):
        dialog = StyledInputDialog(self, title, prompt, is_multiline)
        if dialog.exec_() == QDialog.Accepted:
            return dialog.get_value(), True
        return "", False

    def show_captcha_dialog(self, worker):
        """显示验证码输入弹窗，用户输入后通知等待中的工作线程"""
        if not self.is_running or not worker.is_running or self._closing:
            return
        course_label = getattr(worker, 'course_id', None) or getattr(worker, 'course_code', '')
        dialog = CaptchaDialog(self, worker.cookies, caption=course_label)
        stop_timer = QTimer(dialog)
        stop_timer.timeout.connect(lambda: dialog.reject() if not worker.is_running or self._closing else None)
        stop_timer.start(200)
        if dialog.exec_() == QDialog.Accepted:
            worker.captcha_code = dialog.get_value()
        else:
            worker.captcha_code = "1234"  # 取消则用默认值
        worker.captcha_event.set()
        stop_timer.stop()
        dialog.deleteLater()
    
    def closeEvent(self, event):
        cookie_busy = self.cookie_worker is not None and self.cookie_worker.isRunning()
        query_busy = (self.query_panel is not None and self.query_panel.fetch_thread is not None
                      and self.query_panel.fetch_thread.isRunning())
        captcha_dialogs = self.findChildren(CaptchaDialog)
        captcha_busy = any(dialog.image_worker is not None for dialog in captcha_dialogs)
        if self._managed_workers or cookie_busy or query_busy or captcha_busy:
            event.ignore()
            self._closing = True
            self.schedule_timer.stop()
            self._close_timer.start()
            if self.cookie_worker is not None:
                self.cookie_worker.stop()
            if query_busy:
                self.query_panel.fetch_thread.stop()
            for dialog in captcha_dialogs:
                dialog.reject()
            if self.is_running:
                self.stop_selection()
            self._update_run_state()
            return
        self._close_timer.stop()
        self.log_display.flush()
        event.accept()

    PICKUP_DATA_FILE = "courses_full.json"

    def _load_pickup_course_map(self):
        """从 courses_full.json 加载 cttId → kcbh 映射及课程名称"""
        if not os.path.exists(self.PICKUP_DATA_FILE):
            return {}
        try:
            with open(self.PICKUP_DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            return {}
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
        if self.is_running or self._stopping or self._closing:
            return
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
                "请先运行 course_fetcher.py 生成开课数据文件。")
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
                "请确认课程ID (cttId) 正确，或重新运行 course_fetcher.py。")
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

        for index, kcbh in enumerate(sorted(selected.keys())):
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
            self._queue_worker(worker, index * 500)

        self._update_run_state()
        self.log_display.append(f"✅ 捡漏监控已启动，共 {len(selected)} 个线程")

    def upgrade_course_dialog(self):
        """升级课程：监控多个备选目标，任一出现空位即尝试升级。"""
        if self.is_running or self._stopping or self._closing:
            return
        u = self.user_combo.currentText()
        if not u:
            QMessageBox.warning(self, "错误", "请先选择一个抢课人")
            return

        # ── 检查数据文件 ──
        if not os.path.exists(self.PICKUP_DATA_FILE):
            QMessageBox.warning(self, "提示",
                f"未找到 {self.PICKUP_DATA_FILE}，请先运行 course_fetcher.py。")
            return

        cookies = load_cookies_dict().get(u, "")
        if not cookies:
            QMessageBox.warning(self, "错误", "未找到 Cookie，请先更新！")
            return

        # ── 输入当前课程和多个备选目标 ──
        current_ctt, ok1 = self._get_text_input("升级课程 — 第一步",
            "请输入当前已选课程的课程编号 (cttId)：\n"
            "（这是你想退掉的已选课程）")
        if not ok1 or not current_ctt:
            return
        current_ctt = current_ctt.strip()

        target_text, ok2 = self._get_text_input("升级课程 — 第二步",
            "请输入备选升级课程的课程编号 (cttId)，每行一个，也可用逗号或空格分隔：\n"
            "（任一课程出现空位后，自动退当前课并尝试选入）", is_multiline=True)
        if not ok2 or not target_text.strip():
            return
        target_ctt_ids = list(dict.fromkeys(
            ctt_id for ctt_id in re.split(r"[\s,，;；]+", target_text.strip()) if ctt_id
        ))

        if current_ctt in target_ctt_ids:
            QMessageBox.warning(self, "错误", "当前课程与目标课程相同，无需升级")
            return

        # ── 查找课程名称供确认 ──
        ctt_map = self._load_pickup_course_map()
        current_info = ctt_map.get(current_ctt)
        target_infos = {ctt_id: ctt_map.get(ctt_id) for ctt_id in target_ctt_ids}
        unknown_targets = [ctt_id for ctt_id, info in target_infos.items() if info is None]
        if unknown_targets:
            QMessageBox.warning(
                self, "未找到课程",
                f"以下备选课程未在 {self.PICKUP_DATA_FILE} 中找到：\n"
                f"{'、'.join(unknown_targets)}\n\n请先重新拉取课表后再启动升级监控。",
            )
            return

        current_name = f"{current_info['kcmc']} ({current_ctt})" if current_info else current_ctt
        target_summary = "\n".join(
            f"• {target_infos[ctt_id]['kcmc']} ({ctt_id})"
            for ctt_id in target_ctt_ids
        )

        # ── 确认 ──
        reply = QMessageBox.question(self, "确认升级",
            f"将为 [{u}] 启动升级监控：\n\n"
            f"🔴 当前课程: {current_name}\n"
            f"🟢 备选课程：\n{target_summary}\n\n"
            f"流程：任一备选课程有空位 → 退掉当前课程 → 选入该备选课程\n"
            f"间隔: {self.request_interval}秒\n\n"
            f"是否继续？",
            QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        # ── 启动升级线程 ──
        self.is_running = True
        self.apply_glassmorphism_style()

        worker = UpgradeWorker(
            cookies, u, current_ctt, target_ctt_ids,
            self.request_interval, self.push_token
        )
        worker.log_signal.connect(self.log_display.append)
        worker.success_signal.connect(lambda msg: self.log_display.append(f"🎉 {msg}"))
        worker.captcha_signal.connect(lambda w=worker: self.show_captcha_dialog(w))
        self.upgrade_workers.append(worker)
        self._queue_worker(worker)

        self.log_display.append(f"\n{'='*45}")
        self.log_display.append(f"🆙 升级监控已启动")
        self.log_display.append(f"  当前: {current_name}")
        self.log_display.append(f"  备选: {'；'.join(target_ctt_ids)}")
        self.log_display.append(f"{'='*45}")

        self.tabs.setCurrentIndex(1)
