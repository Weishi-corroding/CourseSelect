# -*- coding: utf-8 -*-
"""
开课数据图形化查询工具 — Glassmorphism UI
读取 courses_full.json，提供多条件筛选：
  - 课程代码（前缀匹配）
  - 开课校区（松江 / 延安路）
  - 是否未录满
  - 上课时间（星期 + 节次）
"""

import sys
import os
import json
import re
import time

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QSizePolicy, QStatusBar, QAbstractItemView, QGroupBox,
    QGridLayout, QMessageBox, QFileDialog, QSplitter,
    QInputDialog, QAction, QDialog, QProgressBar, QTextEdit,
)
from PyQt5.QtGui import QFont, QColor, QBrush, QCursor
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal

# ── 抓取课程线程 ─────────────────────────────────────────────────────
from fetch_courses import (
    fetch_course_list, fetch_course_timetable, load_cookies_dict,
    _common_headers, SessionExpired,
)
# 自动重新登录依赖
from core import get_cookies, load_accounts, save_cookies_dict

# 自动重新登录用的默认账号（匹配 accounts.json 中的 name 字段）
AUTO_RELOGIN_ACCOUNT_NAME = "卫宁远"


class FetchCoursesThread(QThread):
    """后台抓取课程，完成后自动保存到 courses_full.json"""
    progress = pyqtSignal(str)
    progress_step = pyqtSignal(int, int, str)  # (current_1based, total, label)；total=0 表示忙碌/不确定
    finished_signal = pyqtSignal(object)  # dict: 完整数据
    error_signal = pyqtSignal(str)

    def __init__(self, cookie_str, course_codes=None, term_id=88):
        super().__init__()
        self.cookie_str = cookie_str
        self.course_codes = course_codes   # None=全部, [list]=指定课程代码
        self.term_id = term_id
        self._stop_requested = False
        self._relogin_attempts = 0   # 一次会话内只允许重登一次，防死循环

    def stop(self):
        """请求中断抓取；run() 主循环每次迭代检查此标志"""
        self._stop_requested = True

    # ── 自动重新登录 ─────────────────────────────────────────────────
    def _relogin(self):
        """使用 accounts.json 中 AUTO_RELOGIN_ACCOUNT_NAME 的凭据重新登录，
        更新 self.cookie_str 并写回 cookies.json。失败抛 RuntimeError。"""
        self._relogin_attempts += 1
        accounts = load_accounts()
        acct = next((a for a in accounts if a.get("name") == AUTO_RELOGIN_ACCOUNT_NAME), None)
        if not acct:
            raise RuntimeError(
                f"accounts.json 中未找到默认账号「{AUTO_RELOGIN_ACCOUNT_NAME}」，无法自动重新登录"
            )

        self.progress.emit(f"🔐 检测到 Cookie 失效，正在以「{AUTO_RELOGIN_ACCOUNT_NAME}」自动重新登录…")
        self.progress_step.emit(0, 0, f"🔐 正在重新登录（{AUTO_RELOGIN_ACCOUNT_NAME}）…")

        cookies_list = get_cookies(
            acct["username"], acct["password"],
            report_callback=self.progress.emit,
        )
        if not cookies_list:
            raise RuntimeError("get_cookies 返回空")

        new_cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])

        # 写回 cookies.json（覆盖 AUTO_RELOGIN_ACCOUNT_NAME 这一项，其它保留）
        try:
            all_cookies = load_cookies_dict()
        except Exception:
            all_cookies = {}
        all_cookies[AUTO_RELOGIN_ACCOUNT_NAME] = new_cookie_str
        try:
            save_cookies_dict(all_cookies)
        except Exception as e:
            self.progress.emit(f"⚠️ 新 cookie 已获取但写回 cookies.json 失败: {e}")

        self.cookie_str = new_cookie_str
        self.progress.emit("✅ 重新登录成功，继续抓取…")

    def _call_with_relogin(self, fn, *args, **kwargs):
        """包裹 fetch_course_list / fetch_course_timetable：捕获 SessionExpired
        触发一次自动重登录后重试一次。重登失败或重试仍失败则向上抛。

        约定：被包裹的函数第一个位置参数必须是 cookie 字符串，由本方法
        从 self.cookie_str 实时注入——这样 _relogin 写入的新 cookie 才会
        被重试使用。"""
        try:
            return fn(self.cookie_str, *args, **kwargs)
        except SessionExpired:
            if self._relogin_attempts >= 1:
                raise   # 已重登过一次仍失效，让外层 except 兜底
            self._relogin()
            # 重试一次（用 _relogin 刷新后的 self.cookie_str）
            return fn(self.cookie_str, *args, **kwargs)

    def run(self):
        try:
            self.progress.emit("📡 正在获取课程列表...")
            self.progress_step.emit(0, 0, "📡 获取课程列表中...")
            courses = self._call_with_relogin(
                fetch_course_list, term_id=self.term_id,
            )
            if not courses:
                self.error_signal.emit("❌ 获取课程列表失败（返回为空）")
                return

            # 标准化字段
            normalized = []
            for c in courses:
                normalized.append({
                    "id": c.get("id", ""),
                    "kcbh": c.get("kcbh", ""),
                    "kcmc": c.get("kcmc", ""),
                    "xf": c.get("xf", ""),
                    "orgname": c.get("orgname", ""),
                    "jxdg_url": c.get("jxdg_url", ""),
                    "jxrl_url": c.get("jxrl_url", ""),
                })

            # 如果指定了课程代码/编号，只抓取这些
            if self.course_codes is not None:
                known_kcbh = {c["kcbh"] for c in normalized}
                # 分离出已知的课程代码和待解析的编号
                kcbh_to_fetch = {c for c in self.course_codes if c in known_kcbh}
                unresolved = [c for c in self.course_codes if c not in known_kcbh]

                if unresolved:
                    self.progress.emit(f"🔍 正在解析课程编号(cttId): {unresolved}...")
                    ctt_map = self._build_ctt_map()
                    for code in unresolved:
                        if code in ctt_map:
                            kcbh = ctt_map[code]
                            kcbh_to_fetch.add(kcbh)
                            self.progress.emit(f"  cttId {code} → kcbh {kcbh}")
                        else:
                            self.error_signal.emit(
                                f"❌ 无法识别: {code}（不是课程代码，也非已知课程编号）")
                            return

                filtered = [c for c in normalized if c["kcbh"] in kcbh_to_fetch]
                skipped = len(normalized) - len(filtered)
                normalized = filtered
                if not normalized:
                    self.error_signal.emit("❌ 未找到指定的课程代码/编号")
                    return
                if skipped:
                    self.progress.emit(f"⏭️ 跳过了 {skipped} 门未匹配的课程")

            # 逐门获取详细开课信息
            total = len(normalized)
            self.progress.emit(f"🚀 开始获取 {total} 门课程的详细信息...")

            results = []
            cancelled = False
            for i, course in enumerate(normalized):
                if self._stop_requested:
                    cancelled = True
                    self.progress.emit("⏹ 用户已取消抓取，停止后续请求")
                    break

                kcbh = course["kcbh"]
                kcmc = course["kcmc"]
                self.progress.emit(f"  [{i+1}/{total}] {kcbh} {kcmc}")
                self.progress_step.emit(i + 1, total, f"{kcbh} {kcmc}")

                timetable = self._call_with_relogin(
                    fetch_course_timetable, kcbh, term_id=self.term_id,
                )
                results.append({**course, "timetable": timetable})

                # 礼貌性延迟
                if i < total - 1:
                    self.msleep(300)

            if cancelled:
                # 取消时不写文件、不发 finished_signal；仅作为 error_signal 路径之外的中性结束
                self.error_signal.emit("⏹ 抓取已取消（未写入 courses_full.json）")
                return

            # 组装输出
            output = {
                "meta": {
                    "term_id": self.term_id,
                    "fetch_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_courses": len(normalized),
                    "fetched_detail_count": len(results),
                },
                "courses": results,
            }

            # 保存到默认文件
            output_path = "courses_full.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output, f, ensure_ascii=False, indent=2)

            self.progress.emit(f"✅ 抓取完成！{len(results)} 门课程已保存到 {output_path}")
            self.finished_signal.emit(output)

        except Exception as e:
            self.error_signal.emit(f"❌ 抓取异常: {e}")

    def _build_ctt_map(self):
        """从现有的 courses_full.json 构建 cttId → kcbh 映射"""
        path = "courses_full.json"
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            mapping = {}
            for course in data.get("courses", []):
                kcbh = course.get("kcbh", "")
                tt = course.get("timetable")
                if not tt:
                    continue
                for cls in tt.get("classes", []):
                    ctt = cls.get("cttId")
                    if ctt:
                        mapping[str(ctt)] = kcbh
            return mapping
        except:
            return {}

DATA_FILE = "courses_full.json"


class FetchProgressDialog(QDialog):
    """全量/指定课程抓取的实时进度弹窗。

    镜像 modern_ui_production.py 中 CaptchaDialog / StyledInputDialog 的样式约定：
    从 parent 读取 dark_mode，使用相同的紫色/蓝色渐变和按钮主题色。
    """
    def __init__(self, parent, thread):
        super().__init__(parent)
        self.thread = thread
        self.dark_mode = getattr(parent, 'dark_mode', True)
        self._finished = False  # 完成/出错后切换按钮行为

        self.setWindowTitle("🌐 正在抓取课程数据")
        self.setObjectName("FetchProgressDialog")
        self.setMinimumSize(520, 380)
        self.setWindowModality(Qt.ApplicationModal)
        # 去掉右上角关闭按钮，只能通过底部按钮关闭，防止误关闭后线程仍在跑
        self.setWindowFlags(
            (self.windowFlags() | Qt.WindowTitleHint)
            & ~Qt.WindowCloseButtonHint
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 标题
        title = QLabel("🌐 课程数据抓取进度")
        title_font = QFont()
        title_font.setPointSize(13)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # 当前状态（正在抓什么）
        self.status_label = QLabel("准备开始...")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # 进度条 + 计数
        bar_row = QHBoxLayout()
        bar_row.setSpacing(10)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 初始忙碌态
        self.progress_bar.setTextVisible(True)
        bar_row.addWidget(self.progress_bar, 1)

        self.count_label = QLabel("— / —")
        self.count_label.setMinimumWidth(80)
        self.count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        bar_row.addWidget(self.count_label)
        layout.addLayout(bar_row)

        # 日志区
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.log_view, 1)

        # 底部按钮
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        self.btn = QPushButton("取消")
        self.btn.setMinimumWidth(100)
        self.btn.clicked.connect(self._on_btn_clicked)
        btn_row.addWidget(self.btn)
        layout.addLayout(btn_row)

        self._apply_style()

    # ── 槽函数 ───────────────────────────────────────────────────────
    def on_step(self, current, total, label):
        """结构化进度信号入口：current=1基索引，total=总数（0 表示未知/忙碌），label=当前条目"""
        if total > 0:
            if self.progress_bar.maximum() != total:
                self.progress_bar.setRange(0, total)
            self.progress_bar.setValue(current)
            self.count_label.setText(f"{current} / {total}")
            self.status_label.setText(f"正在抓取：{label}")
        else:
            # 维持忙碌态
            self.progress_bar.setRange(0, 0)
            self.count_label.setText("— / —")
            self.status_label.setText(label)

    def on_log(self, msg):
        """文本进度信号入口：累加到日志区，自动滚到底"""
        self.log_view.append(msg)
        sb = self.log_view.verticalScrollBar()
        sb.setValue(sb.maximum())

    def on_finished(self, _data):
        self._finished = True
        # 进度条置满（若已知 total）
        if self.progress_bar.maximum() > 0:
            self.progress_bar.setValue(self.progress_bar.maximum())
        else:
            self.progress_bar.setRange(0, 1)
            self.progress_bar.setValue(1)
        self.status_label.setText("✅ 抓取完成")
        self.btn.setText("关闭")
        self.btn.setEnabled(True)
        # 允许窗口栏关闭按钮可用（如果系统重新加上）
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)
        self.show()  # 重应用 windowFlags 需要重新 show

    def on_error(self, msg):
        self._finished = True
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.status_label.setText("❌ 抓取中断 / 出错")
        self.log_view.append(msg)
        self.btn.setText("关闭")
        self.btn.setEnabled(True)
        self.setWindowFlags(self.windowFlags() | Qt.WindowCloseButtonHint)
        self.show()

    def _on_btn_clicked(self):
        if self._finished:
            self.accept()
            return
        # 线程仍在跑 → 请求中断
        if self.thread is not None:
            try:
                self.thread.stop()
            except Exception:
                pass
        self.btn.setText("正在取消…")
        self.btn.setEnabled(False)
        self.status_label.setText("⏹ 正在取消，等待当前请求结束…")

    def closeEvent(self, event):
        # 只允许在 _finished 后通过窗口关闭按钮关闭
        if self._finished:
            event.accept()
        else:
            event.ignore()

    def keyPressEvent(self, event):
        # ESC 等同点击按钮：未完成时走"取消"，完成后才允许关闭
        if event.key() == Qt.Key_Escape:
            self._on_btn_clicked()
            return
        super().keyPressEvent(event)

    # ── 样式 ──────────────────────────────────────────────────────────
    def _apply_style(self):
        if self.dark_mode:
            self.setStyleSheet("""
                QDialog#FetchProgressDialog {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #202040, stop:0.5 #1a1a2e, stop:1 #202060);
                    color: white;
                }
                QDialog#FetchProgressDialog QLabel {
                    color: white;
                    background: transparent;
                }
                QDialog#FetchProgressDialog QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #4B0082, stop:1 #483D8B);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QDialog#FetchProgressDialog QPushButton:hover {
                    background: #6A5ACD;
                }
                QDialog#FetchProgressDialog QPushButton:disabled {
                    background: #3a3a5e;
                    color: #aaaaaa;
                }
                QDialog#FetchProgressDialog QProgressBar {
                    border: 1px solid #4B0082;
                    border-radius: 6px;
                    background: rgba(255, 255, 255, 0.08);
                    color: white;
                    text-align: center;
                    height: 22px;
                }
                QDialog#FetchProgressDialog QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #4B0082, stop:1 #6A5ACD);
                    border-radius: 5px;
                }
                QDialog#FetchProgressDialog QTextEdit {
                    background: rgba(0, 0, 0, 0.25);
                    color: #e8e8f5;
                    border: 1px solid #4B0082;
                    border-radius: 6px;
                    padding: 6px;
                    font-family: Consolas, "Courier New", monospace;
                    font-size: 11px;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog#FetchProgressDialog {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                        stop:0 #F0F3F9, stop:0.5 #E6EAF0, stop:1 #DCE4F0);
                    color: #202020;
                }
                QDialog#FetchProgressDialog QLabel {
                    color: #202020;
                    background: transparent;
                }
                QDialog#FetchProgressDialog QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #3B82F6, stop:1 #2563EB);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QDialog#FetchProgressDialog QPushButton:hover {
                    background: #1D4ED8;
                }
                QDialog#FetchProgressDialog QPushButton:disabled {
                    background: #c0c8d6;
                    color: #ffffff;
                }
                QDialog#FetchProgressDialog QProgressBar {
                    border: 1px solid #3B82F6;
                    border-radius: 6px;
                    background: rgba(255, 255, 255, 0.6);
                    color: #1f2937;
                    text-align: center;
                    height: 22px;
                }
                QDialog#FetchProgressDialog QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #3B82F6, stop:1 #2563EB);
                    border-radius: 5px;
                }
                QDialog#FetchProgressDialog QTextEdit {
                    background: rgba(255, 255, 255, 0.7);
                    color: #1f2937;
                    border: 1px solid #3B82F6;
                    border-radius: 6px;
                    padding: 6px;
                    font-family: Consolas, "Courier New", monospace;
                    font-size: 11px;
                }
            """)


# ── 星期映射 ──────────────────────────────────────────────────────
DAY_MAP = {
    "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "日": 7,
}
DAY_REVERSE = {v: k for k, v in DAY_MAP.items()}
DAY_OPTIONS = ["全部", "周一", "周二", "周三", "周四", "周五", "周六", "周日"]

# ── 数据辅助函数 ──────────────────────────────────────────────────
def load_courses(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_time_slot(text):
    """解析 "周五.5.6.7节" → (day=5, periods=[5,6,7])"""
    m = re.match(r"周([一二三四五六日])\.([\d.]+)节", text.strip())
    if not m:
        return None, []
    day = DAY_MAP.get(m.group(1))
    periods = [int(x) for x in m.group(2).split(".")]
    return day, periods


def detect_campus(classroom):
    """根据教室名判断校区（兜底法：仅在 suggested_major 不可用时使用）。

    DHU 主要两个校区命名约定：
      - 松江校区: 以 '松' 开头，例：松1334、松2138
      - 延安路校区: 多数为数字+'教'，例：1教101、4教310、8教205；
                    少数历史命名直接以 '延' 开头。
    其他（'线上教学'、外部场地等）返回 '' 视为未知。
    """
    if not classroom:
        return ""
    s = classroom.strip()
    if s.startswith("松"):
        return "松江"
    if s.startswith("延"):
        return "延安路"
    # <digit>+教 → 延安路（1教/2教/3教/4教/8教 等）
    if re.match(r"^\d+教", s):
        return "延安路"
    return ""


def detect_campus_from_major(suggested_major):
    """从「建议优选专业」字段抽取校区。

    部分课程（尤其是公共课）此列存的是 "延安路校区" / "松江校区" 这类
    明确的校区名；对专业课则可能是具体专业名（如 "信息工程"），抽不到
    返回 ''，由调用方回退到 detect_campus 用教室兜底。
    """
    if not suggested_major:
        return ""
    s = suggested_major
    if "松江" in s:
        return "松江"
    if "延安路" in s:
        return "延安路"
    return ""


def class_campus(cls):
    """优先 suggested_major，回退到第一条 schedule 的教室"""
    by_major = detect_campus_from_major(cls.get("suggested_major", ""))
    if by_major:
        return by_major
    for sch in (cls.get("schedule") or []):
        c = detect_campus(sch.get("classroom", ""))
        if c:
            return c
    return ""


# ── 查询引擎 ──────────────────────────────────────────────────────
class CourseQueryEngine:
    def __init__(self, data):
        self.courses = data.get("courses", [])

    def query(self, course_code_prefix="", course_name_keyword="", campus="", only_available=False,
              day_filter=0, period_filter=0, teacher_keyword=""):
        """
        核心筛选逻辑。
        day_filter: 0=全部, 1-7=周一到周日
        period_filter: 0=全部, 1-13=具体节次
        teacher_keyword: 教师姓名部分匹配（不区分大小写，作用在班级层级）
        """
        results = []
        teacher_kw = teacher_keyword.strip().lower()

        for course in self.courses:
            kcbh = course.get("kcbh", "")
            kcmc = course.get("kcmc", "")
            xf = course.get("xf", "")
            orgname = course.get("orgname", "")

            # 课程代码前缀匹配
            if course_code_prefix:
                if not kcbh.startswith(course_code_prefix):
                    continue

            # 课程名称部分匹配
            if course_name_keyword:
                if course_name_keyword not in kcmc:
                    continue

            timetable = course.get("timetable")
            if not timetable:
                continue
            classes = timetable.get("classes", [])
            if not classes:
                continue

            for cls in classes:
                enroll_cnt = cls.get("enrollCnt", 0)
                max_cnt = cls.get("maxCnt", 0)

                # 教师姓名部分匹配（班级粒度，不区分大小写）
                if teacher_kw:
                    teacher_name = (cls.get("teacher_name", "") or "").lower()
                    if teacher_kw not in teacher_name:
                        continue

                # 未录满筛选
                if only_available and enroll_cnt >= max_cnt:
                    continue

                # 解析调度信息
                schedules = cls.get("schedule", [])
                schedules = schedules or []

                # 时间筛选：只要该班级任一 schedule 匹配即保留
                if day_filter > 0 or period_filter > 0:
                    # 校区筛选（班级级别，优先 suggested_major 字段）
                    cls_campus = class_campus(cls)
                    if campus and cls_campus and cls_campus != campus:
                        continue

                    matched = False
                    for sch in schedules:
                        day, periods = parse_time_slot(sch.get("time_slot", ""))

                        # 星期匹配
                        if day_filter > 0:
                            if day != day_filter:
                                continue

                        # 节次匹配
                        if period_filter > 0:
                            if period_filter not in periods:
                                continue

                        matched = True
                        break

                    if not matched:
                        if day_filter > 0 or period_filter > 0:
                            continue
                else:
                    # 校区筛选（无时间筛选时，班级级别优先 suggested_major 字段）
                    if campus:
                        cls_campus = class_campus(cls)
                        if cls_campus and cls_campus != campus:
                            continue

                # 构建显示用时间字符串
                time_str = " | ".join(
                    f"{s.get('weeks','')} {s.get('time_slot','')} @{s.get('classroom','')}"
                    for s in schedules
                ) if schedules else "无排课信息"

                results.append({
                    "kcbh": kcbh,
                    "kcmc": kcmc,
                    "xf": xf,
                    "id": course.get("id", ""),
                    "orgname": orgname,
                    "classNo": cls.get("classNo", ""),
                    "cttId": cls.get("cttId", ""),
                    "maxCnt": max_cnt,
                    "enrollCnt": enroll_cnt,
                    "applyCnt": cls.get("applyCnt", 0),
                    "teacher": cls.get("teacher_name", ""),
                    "schedule": time_str,
                    "campus": class_campus(cls),
                })

        return results


# ── UI ─────────────────────────────────────────────────────────────
class CourseQueryUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = None
        self.engine = None
        self.dark_mode = True

        self.setObjectName("MainWindow")
        self.setWindowTitle("📖 开课数据查询工具")
        self.setGeometry(80, 80, 1300, 850)
        self.setMinimumSize(1000, 700)

        self._setup_ui()
        self._setup_menu()
        self._apply_style()

        self.statusBar().showMessage("就绪 | 文件: 未加载")

    # ── UI 构建 ────────────────────────────────────────────────
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(25, 20, 25, 20)
        main_layout.setSpacing(15)

        # ── 标题 ──
        title = QLabel("📖 开课数据查询")
        title.setFont(QFont("Microsoft YaHei UI", 22, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        # ── 筛选面板 ──
        filter_group = QGroupBox("筛选条件")
        filter_group.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
        filter_layout = QGridLayout(filter_group)
        filter_layout.setSpacing(12)
        filter_layout.setContentsMargins(15, 20, 15, 15)

        # 第一行：课程代码 / 课程名称 / 未录满
        filter_layout.addWidget(QLabel("课程代码:"), 0, 0)
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("前缀匹配，如 030")
        self.code_input.setFont(QFont("Microsoft YaHei UI", 11))
        self.code_input.setMinimumHeight(34)
        self.code_input.returnPressed.connect(self._do_query)
        filter_layout.addWidget(self.code_input, 0, 1)

        filter_layout.addWidget(QLabel("课程名称:"), 0, 2)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("部分匹配，如 电路")
        self.name_input.setFont(QFont("Microsoft YaHei UI", 11))
        self.name_input.setMinimumHeight(34)
        self.name_input.returnPressed.connect(self._do_query)
        filter_layout.addWidget(self.name_input, 0, 3)

        self.avail_check = QCheckBox("仅显示未录满")
        self.avail_check.setFont(QFont("Microsoft YaHei UI", 11))
        filter_layout.addWidget(self.avail_check, 0, 4, 1, 2)

        # 第二行：上课时间 / 节次 / 开课校区
        filter_layout.addWidget(QLabel("上课时间:"), 1, 0)
        self.day_combo = QComboBox()
        self.day_combo.addItems(DAY_OPTIONS)
        self.day_combo.setFont(QFont("Microsoft YaHei UI", 11))
        self.day_combo.setMinimumHeight(34)
        filter_layout.addWidget(self.day_combo, 1, 1)

        filter_layout.addWidget(QLabel("第"), 1, 2)
        self.period_combo = QComboBox()
        self.period_combo.addItems(["全部"] + [f"{i}节" for i in range(1, 14)])
        self.period_combo.setFont(QFont("Microsoft YaHei UI", 11))
        self.period_combo.setMinimumHeight(34)
        filter_layout.addWidget(self.period_combo, 1, 3)

        filter_layout.addWidget(QLabel("开课校区:"), 1, 4)
        self.campus_combo = QComboBox()
        self.campus_combo.addItems(["全部", "松江", "延安路"])
        self.campus_combo.setFont(QFont("Microsoft YaHei UI", 11))
        self.campus_combo.setMinimumHeight(34)
        filter_layout.addWidget(self.campus_combo, 1, 5)

        # 第三行：教师姓名
        filter_layout.addWidget(QLabel("教师姓名:"), 2, 0)
        self.teacher_input = QLineEdit()
        self.teacher_input.setPlaceholderText("部分匹配，如 王")
        self.teacher_input.setFont(QFont("Microsoft YaHei UI", 11))
        self.teacher_input.setMinimumHeight(34)
        self.teacher_input.returnPressed.connect(self._do_query)
        filter_layout.addWidget(self.teacher_input, 2, 1)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.query_btn = QPushButton("🔍 查询")
        self.query_btn.setFont(QFont("Microsoft YaHei UI", 13, QFont.Bold))
        self.query_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.query_btn.setMinimumSize(140, 42)
        self.query_btn.clicked.connect(self._do_query)
        btn_layout.addWidget(self.query_btn)

        self.reset_btn = QPushButton("↺ 重置")
        self.reset_btn.setFont(QFont("Microsoft YaHei UI", 13))
        self.reset_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.reset_btn.setMinimumSize(120, 42)
        self.reset_btn.clicked.connect(self._do_reset)
        btn_layout.addWidget(self.reset_btn)

        filter_layout.addLayout(btn_layout, 2, 0, 1, 6)
        main_layout.addWidget(filter_group)

        # ── 结果统计 ──
        self.count_label = QLabel("共查询到 0 条结果")
        self.count_label.setFont(QFont("Microsoft YaHei UI", 12))
        main_layout.addWidget(self.count_label)

        # ── 结果表格 ──
        self.table = QTableWidget()
        self.table.setFont(QFont("Microsoft YaHei UI", 10))
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)

        headers = [
            ("课程代码", 100), ("课程编号", 70), ("课程名称", 200), ("学分", 50),
            ("班级", 55), ("容量", 65),
            ("已申请", 55), ("已录取", 55), ("余量", 55),
            ("教师", 100), ("校区", 60), ("上课时间", 350),
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels([h[0] for h in headers])
        self.header = self.table.horizontalHeader()
        for i, (_, w) in enumerate(headers):
            self.header.setSectionResizeMode(i, QHeaderView.Interactive)
            self.table.setColumnWidth(i, w)
        # 上课时间列可伸缩
        self.header.setSectionResizeMode(11, QHeaderView.Stretch)

        self.table.setMinimumHeight(300)
        main_layout.addWidget(self.table, 1)

    # ── 样式 ────────────────────────────────────────────────────
    def _apply_style(self):
        if self.dark_mode:
            colors = {
                "bg_start": "#202040", "bg_mid": "#1a1a2e", "bg_end": "#202060",
                "text": "#FFFFFF", "card": "rgba(255,255,255,0.08)",
                "card_border": "rgba(255,255,255,0.15)",
                "input": "rgba(0,0,0,0.2)", "btn1": "#4B0082", "btn2": "#483D8B",
                "btn_hover": "#6A5ACD", "table_bg": "rgba(0,0,0,0.15)",
                "table_alt": "rgba(255,255,255,0.04)",
                "table_sel": "rgba(0,198,255,0.25)",
                "group_bg": "rgba(255,255,255,0.06)",
                "available_fg": "#00FF7F",
                "full_fg": "#FF6B6B",
                "scroll_bg": "rgba(255,255,255,0.05)",
                "scroll_handle": "rgba(255,255,255,0.2)",
                "header_bg": "#2D2D5E",
                "header_text": "#FFFFFF",
            }
        else:
            colors = {
                "bg_start": "#F0F3F9", "bg_mid": "#E6EAF0", "bg_end": "#DCE4F0",
                "text": "#202020", "card": "rgba(255,255,255,0.75)",
                "card_border": "rgba(0,0,0,0.08)",
                "input": "#FFFFFF", "btn1": "#3B82F6", "btn2": "#2563EB",
                "btn_hover": "#2563EB", "table_bg": "#FFFFFF",
                "table_alt": "rgba(0,0,0,0.02)",
                "table_sel": "rgba(59,130,246,0.15)",
                "group_bg": "rgba(255,255,255,0.6)",
                "available_fg": "#16A34A",
                "full_fg": "#DC2626",
                "scroll_bg": "#F0F0F0",
                "scroll_handle": "#C0C0C0",
                "header_bg": "#D6DAE2",
                "header_text": "#202020",
            }

        self.avail_colors = (colors["available_fg"], colors["full_fg"])
        qss = f"""
        QMainWindow#MainWindow {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {colors['bg_start']}, stop:0.5 {colors['bg_mid']}, stop:1 {colors['bg_end']});
        }}
        QLabel {{ color: {colors['text']}; background: transparent; }}
        QGroupBox {{
            background-color: {colors['group_bg']};
            border: 1px solid {colors['card_border']};
            border-radius: 10px; margin-top: 12px;
            font-weight: bold; color: {colors['text']};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin; subcontrol-position: top left;
            padding: 2px 10px;
        }}
        QLineEdit, QComboBox {{
            background-color: {colors['input']};
            border: 1px solid {colors['card_border']};
            border-radius: 6px; padding: 4px 8px;
            color: {colors['text']};
            selection-background-color: {colors['btn1']};
        }}
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox QAbstractItemView {{
            background-color: {colors['input']};
            color: {colors['text']};
            selection-background-color: {colors['btn1']};
        }}
        QCheckBox {{
            color: {colors['text']}; spacing: 8px;
        }}
        QCheckBox::indicator {{
            width: 18px; height: 18px;
            border: 1px solid {colors['card_border']};
            border-radius: 4px; background-color: {colors['input']};
        }}
        QCheckBox::indicator:checked {{
            background-color: {colors['btn1']};
            border-color: {colors['btn1']};
        }}
        QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {colors['btn1']}, stop:1 {colors['btn2']});
            color: #FFFFFF; border: none; border-radius: 8px; padding: 6px 18px;
        }}
        QPushButton:hover {{ background-color: {colors['btn_hover']}; }}
        QMenuBar {{
            background-color: {colors['header_bg']};
            color: {colors['header_text']};
            border: none;
            padding: 2px;
        }}
        QMenuBar::item {{
            color: {colors['header_text']};
            padding: 4px 12px;
            border-radius: 4px;
        }}
        QMenuBar::item:selected {{
            background-color: {colors['btn1']};
        }}
        QMenu {{
            background-color: {colors['input']};
            color: {colors['text']};
            border: 1px solid {colors['card_border']};
            border-radius: 6px;
            padding: 4px;
        }}
        QMenu::item {{
            padding: 6px 24px 6px 12px;
            border-radius: 4px;
        }}
        QMenu::item:selected {{
            background-color: {colors['btn1']};
            color: #FFFFFF;
        }}
        QMenu::separator {{
            height: 1px;
            background: {colors['card_border']};
            margin: 4px 8px;
        }}
        QTableWidget {{
            background-color: {colors['table_bg']};
            alternate-background-color: {colors['table_alt']};
            border: 1px solid {colors['card_border']};
            border-radius: 8px; gridline-color: {colors['card_border']};
            color: {colors['text']};
        }}
        QTableWidget::item:selected {{
            background-color: {colors['table_sel']};
        }}
        QHeaderView::section {{
            background-color: {colors['header_bg']};
            color: {colors['header_text']};
            padding: 6px; border: none;
            border-bottom: 1px solid {colors['card_border']};
            border-right: 1px solid {colors['card_border']};
            font-weight: bold;
        }}
        QHeaderView::section:vertical {{
            background-color: {colors['header_bg']};
            color: {colors['header_text']};
            padding: 2px 6px; border: none;
            border-bottom: 1px solid {colors['card_border']};
            border-right: 1px solid {colors['card_border']};
        }}
        QTableCornerButton::section {{
            background-color: {colors['header_bg']};
            border: none;
            border-bottom: 1px solid {colors['card_border']};
            border-right: 1px solid {colors['card_border']};
        }}
        QStatusBar {{ color: {colors['text']}; background: transparent; }}
        QScrollBar:vertical {{
            background: {colors['scroll_bg']}; width: 10px; border-radius: 5px;
        }}
        QScrollBar::handle:vertical {{
            background: {colors['scroll_handle']}; border-radius: 5px; min-height: 30px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QMessageBox {{
            background-color: {colors['bg_mid']};
            color: {colors['text']};
        }}
        QMessageBox QLabel {{
            color: {colors['text']};
            font-size: 13px;
        }}
        QMessageBox QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 {colors['btn1']}, stop:1 {colors['btn2']});
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
        """
        self.setStyleSheet(qss)

    # ── 菜单栏 ───────────────────────────────────────────────────
    def _setup_menu(self):
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("📂 文件")
        file_menu.addAction("📂 导入文件...", self._do_load)

        file_menu.addSeparator()
        file_menu.addAction("❌ 退出", self.close)

        # 数据菜单
        data_menu = menubar.addMenu("🌐 数据")
        data_menu.addAction("🌐 重新抓取全部课程", self._do_fetch_all)
        data_menu.addAction("🎯 抓取指定课程...", self._do_fetch_specific)

    # ── 抓取操作 ─────────────────────────────────────────────────
    def _do_fetch_all(self):
        """抓取全部课程"""
        reply = QMessageBox.question(
            self, "确认抓取",
            "即将从教务系统重新抓取全部课程的详细开课信息。\n"
            "此过程需要较长时间，请确保网络连接正常。\n\n"
            "继续吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return
        self._start_fetch()

    def _do_fetch_specific(self):
        """弹出对话框让用户输入课程代码或编号，只抓取这几门"""
        code_text, ok = QInputDialog.getText(
            self, "抓取指定课程",
            "输入课程代码(kcbh)或课程编号(cttId)，多个用逗号或空格分隔：\n"
            "（输编号会自动查找对应的课程代码）:",
            text=""
        )
        if not ok or not code_text.strip():
            return
        codes = [c.strip() for c in code_text.replace(",", " ").split() if c.strip()]
        if not codes:
            return
        reply = QMessageBox.question(
            self, "确认抓取",
            f"即将抓取 {len(codes)} 门指定课程的详细信息：\n"
            f"{'、'.join(codes[:10])}{'...' if len(codes) > 10 else ''}\n\n"
            "继续吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return
        self._start_fetch(course_codes=codes)

    def _start_fetch(self, course_codes=None):
        """启动抓取线程"""
        # 获取 cookie
        cookies_dict = load_cookies_dict()
        if not cookies_dict:
            QMessageBox.warning(self, "无 Cookie",
                "cookies.json 为空或不存在。\n请先运行主抢课程序获取有效的 Cookie。")
            return

        user = list(cookies_dict.keys())[0]
        cookie_str = cookies_dict[user]

        # 禁用菜单防止重复点击
        self._set_fetch_menu_enabled(False)

        # 创建并启动线程
        self.fetch_thread = FetchCoursesThread(cookie_str, course_codes=course_codes)

        # 进度弹窗
        self.fetch_dialog = FetchProgressDialog(self, self.fetch_thread)

        # 文本进度：同时进状态栏 / count_label / 弹窗日志
        self.fetch_thread.progress.connect(self._on_fetch_progress)
        self.fetch_thread.progress.connect(self.fetch_dialog.on_log)
        # 结构化进度 → 弹窗进度条
        self.fetch_thread.progress_step.connect(self.fetch_dialog.on_step)
        # 终态：弹窗自己切按钮、主窗口走既有处理
        self.fetch_thread.finished_signal.connect(self.fetch_dialog.on_finished)
        self.fetch_thread.error_signal.connect(self.fetch_dialog.on_error)
        self.fetch_thread.finished_signal.connect(self._on_fetch_finished)
        self.fetch_thread.error_signal.connect(self._on_fetch_error)

        self.fetch_thread.start()
        self.fetch_dialog.show()  # 非阻塞；ApplicationModal 阻断主窗交互
        self.statusBar().showMessage(f"🔄 正在抓取课程数据（用户: {user}）...")

    def _on_fetch_progress(self, msg):
        """抓取进度更新"""
        self.statusBar().showMessage(msg)
        # 也输出到 count_label 方便查看
        self.count_label.setText(msg)

    def _on_fetch_finished(self, data):
        """抓取完成"""
        self._set_fetch_menu_enabled(True)
        self.statusBar().showMessage(f"✅ 抓取完成，共 {len(data.get('courses', []))} 门课程", 5000)
        # 自动加载抓取结果
        self._load_file("courses_full.json")

    def _on_fetch_error(self, msg):
        """抓取出错"""
        self._set_fetch_menu_enabled(True)
        self.statusBar().showMessage("❌ 抓取出错", 5000)
        QMessageBox.critical(self, "抓取出错", msg)

    def _set_fetch_menu_enabled(self, enabled):
        """切换抓取菜单的启用状态"""
        for action in self.menuBar().actions():
            if action.text() == "🌐 数据":
                action.setEnabled(enabled)
                break

    # ── 操作 ────────────────────────────────────────────────────
    def _do_load(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "打开课程数据文件", os.path.dirname(__file__),
            "JSON 文件 (*.json);;所有文件 (*)"
        )
        if path:
            self._load_file(path)

    def _load_file(self, path):
        try:
            self.data = load_courses(path)
            self.engine = CourseQueryEngine(self.data)
            self.statusBar().showMessage(
                f"已加载: {path} | "
                f"共 {len(self.data.get('courses', []))} 门课程",
                5000
            )
            self._do_query()
        except Exception as e:
            QMessageBox.critical(self, "加载错误", f"无法加载文件:\n{e}")

    def _do_query(self):
        if self.engine is None:
            # 自动加载默认文件
            if os.path.exists(DATA_FILE):
                self._load_file(DATA_FILE)
                return
            else:
                self.count_label.setText("⚠️ 请先加载数据文件")
                return

        prefix = self.code_input.text().strip()
        name_keyword = self.name_input.text().strip()
        teacher_keyword = self.teacher_input.text().strip()
        campus_text = self.campus_combo.currentText()
        campus = campus_text if campus_text != "全部" else ""
        only_avail = self.avail_check.isChecked()

        day_text = self.day_combo.currentText()
        day = 0 if day_text == "全部" else DAY_OPTIONS.index(day_text)

        period_text = self.period_combo.currentText()
        period = 0 if period_text == "全部" else int(period_text.replace("节", ""))

        results = self.engine.query(
            course_code_prefix=prefix,
            course_name_keyword=name_keyword,
            campus=campus,
            only_available=only_avail,
            day_filter=day,
            period_filter=period,
            teacher_keyword=teacher_keyword,
        )

        self._populate_table(results)

    def _do_reset(self):
        self.code_input.clear()
        self.name_input.clear()
        self.teacher_input.clear()
        self.campus_combo.setCurrentIndex(0)
        self.avail_check.setChecked(False)
        self.day_combo.setCurrentIndex(0)
        self.period_combo.setCurrentIndex(0)
        self._do_query()

    def _populate_table(self, results):
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(results))
        self.table.setAlternatingRowColors(True)

        for row, r in enumerate(results):
            remaining = r["maxCnt"] - r["enrollCnt"]
            is_full = remaining <= 0

            items = [
                r["kcbh"], r["cttId"], r["kcmc"], str(r["xf"]),
                r["classNo"], str(r["maxCnt"]),
                str(r["enrollCnt"]), str(r["applyCnt"]),
                str(remaining) if remaining >= 0 else "0",
                r["teacher"], r["campus"], r["schedule"],
            ]

            for col, text in enumerate(items):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter if col not in (2, 9, 11) else Qt.AlignLeft | Qt.AlignVCenter)
                if col == 8:  # 余量列
                    fg = self.avail_colors[0] if remaining > 0 else self.avail_colors[1]
                    item.setForeground(QBrush(QColor(fg)))
                    if remaining > 0:
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
                self.table.setItem(row, col, item)

        self.table.setSortingEnabled(True)

        # 统计
        total = len(results)
        total_cap = sum(r["maxCnt"] for r in results)
        total_applied = sum(r["enrollCnt"] for r in results)  # 已申请
        total_enrolled = sum(r["applyCnt"] for r in results)  # 已录取
        avail = sum(1 for r in results if r["maxCnt"] - r["enrollCnt"] > 0)

        prefix = self.code_input.text().strip()
        prefix_info = f" | 前缀: {prefix}" if prefix else ""
        rate_str = f"|  录取率: {total_enrolled / total_cap * 100:.1f}%" if total_cap > 0 else ""
        self.count_label.setText(
            f"共查询到 {total} 条结果{prefix_info}  "
            f"| 未录满: {avail}  |  容量: {total_cap}  "
            f"| 已申请: {total_applied}  |  已录取: {total_enrolled}  {rate_str}"
        )

        self.statusBar().showMessage(
            f"查询完成: {total} 条结果 | {avail} 门可选", 3000
        )


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = CourseQueryUI()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
